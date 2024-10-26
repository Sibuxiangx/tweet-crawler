from datetime import datetime
from typing import Annotated, List, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, Field, field_validator
from typing_extensions import Self


def _twitter_datetime(v: str) -> datetime:
    return datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y")


class TwitterUser(BaseModel):
    id: int
    name: str
    screen_name: str
    location: str
    description: str
    protected: Optional[bool] = None
    verified: bool
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    pinned_tweet_ids: List[int] = []
    profile_image_url_normal: AnyHttpUrl = Field(alias="profile_image_url_https")
    profile_banner_url: Optional[AnyHttpUrl] = None
    followers_count: int
    friends_count: int
    listed_count: int
    favourites_count: int
    statuses_count: int
    followed_by: Optional[bool] = None
    following: Optional[bool] = None
    can_dm: Optional[bool] = None

    @property
    def handle(self):
        return f"@{self.screen_name}"

    @property
    def profile_image_url(self):
        return str(self.profile_image_url_normal).replace("_normal", "")

    @classmethod
    def from_result(cls, result: dict) -> Self:
        return cls.model_validate(result["legacy"] | {"id": result["rest_id"]})


class TweetEntity(BaseModel):
    indices: List[int]


class TweetEntityHashTag(TweetEntity):
    text: str


class TweetEntityMediaPhoto(TweetEntity):
    type: Literal["photo"]
    url: AnyHttpUrl = Field(alias="media_url_https")
    expanded_url: AnyHttpUrl


class TweetEntityMediaVideo(TweetEntity):
    type: Literal["video"]
    url: AnyHttpUrl = Field(alias="video_info")
    expanded_url: AnyHttpUrl

    @field_validator("url", mode="before")  # noqa
    @classmethod
    def __validate_url(cls, v: dict):
        return v["variants"][-1]["url"]


class TweetEntityMediaAnimatedGif(TweetEntity):
    type: Literal["animated_gif"]
    url: AnyHttpUrl = Field(alias="video_info")
    expanded_url: AnyHttpUrl

    @field_validator("url", mode="before")  # noqa
    @classmethod
    def __validate_url(cls, v: dict):
        return v["variants"][-1]["url"]


class TweetEntitySymbol(TweetEntity):
    text: str


class TweetEntityTimestamp(TweetEntity):
    pass


class TweetEntityUrl(TweetEntity):
    display_url: str
    expanded_url: str
    url: str


class TweetEntityUserMention(TweetEntity):
    id: int = Field(alias="id_str")
    name: str
    screen_name: str


class TweetEntities(BaseModel):
    hashtags: List[TweetEntityHashTag] = []
    media: List[
        TweetEntityMediaPhoto | TweetEntityMediaVideo | TweetEntityMediaAnimatedGif
    ] = []
    symbols: List[TweetEntitySymbol] = []
    timestamps: List[TweetEntityTimestamp] = []
    urls: List[TweetEntityUrl] = []
    user_mentions: List[TweetEntityUserMention] = []


class Tweet(BaseModel):
    id: int = Field(alias="id_str")
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    full_text: str
    display_text_range: List[int]
    lang: str
    possibly_sensitive: bool = False
    entities: TweetEntities
    conversation_threads: List[List[Self]] = []
    user: TwitterUser
    views_count: int
    bookmark_count: int
    favorite_count: int
    quote_count: int
    reply_count: int
    retweet_count: int
    bookmarked: bool
    favorited: bool  # noqa
    retweeted: bool

    @property
    def text(self) -> str:
        return self.full_text[self.display_text_range[0] : self.display_text_range[1]]

    @classmethod
    def from_instructions(cls, result: List[dict]) -> Self:
        base_tweet = None
        for instruction in result:
            if instruction["type"] == "TimelineAddEntries":
                entries: List[dict] = instruction["entries"]
                base_tweet = cls.from_entry(entries.pop(0))[0]
                for entry in entries:
                    if entry["entryId"].startswith("tweet-") or entry[
                        "entryId"
                    ].startswith("conversationthread-"):
                        base_tweet.conversation_threads.append(cls.from_entry(entry))
        assert base_tweet
        return base_tweet

    @classmethod
    def from_entry(cls, result: dict) -> List[Self]:
        if result["entryId"].startswith("tweet"):
            return [cls.from_timeline_item(result["content"])]
        else:
            return cls.from_timeline_module(result["content"])

    @classmethod
    def from_timeline_item(cls, result: dict) -> Self:
        item = result["itemContent"]
        assert item["itemType"] == "TimelineTweet"
        return cls.from_result(item["tweet_results"]["result"])

    @classmethod
    def from_timeline_module(cls, result: dict) -> List[Self]:
        return [
            cls.from_result(item["item"]["itemContent"]["tweet_results"]["result"])
            for item in result["items"]
            if "cursor" not in item["entryId"]
        ]

    @classmethod
    def from_result(cls, result: dict) -> Self:
        if result["__typename"] == "TweetWithVisibilityResults":
            result = result["tweet"]
        return cls.model_validate(
            result["legacy"]
            | {
                "views_count": result["views"].get("count", 0),
                "user": TwitterUser.from_result(
                    result["core"]["user_results"]["result"]
                ),
            }
        )
