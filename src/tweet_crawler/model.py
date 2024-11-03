from datetime import datetime
from typing import Annotated, List, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, Field, field_validator
from typing_extensions import Self


def _twitter_datetime(v: str) -> datetime:
    return datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y")


class TwitterEntity(BaseModel):
    indices: List[int]


class TwitterEntityHashTag(TwitterEntity):
    text: str


class TwitterEntityMediaPhoto(TwitterEntity):
    type: Literal["photo"]
    url: AnyHttpUrl = Field(alias="media_url_https")
    expanded_url: AnyHttpUrl


class TwitterEntityMediaVideo(TwitterEntity):
    type: Literal["video"]
    url: AnyHttpUrl = Field(alias="video_info")
    expanded_url: AnyHttpUrl

    @field_validator("url", mode="before")  # noqa
    @classmethod
    def __validate_url(cls, v: dict):
        return v["variants"][-1]["url"]


class TwitterEntityMediaAnimatedGif(TwitterEntity):
    type: Literal["animated_gif"]
    url: AnyHttpUrl = Field(alias="video_info")
    expanded_url: AnyHttpUrl

    @field_validator("url", mode="before")  # noqa
    @classmethod
    def __validate_url(cls, v: dict):
        return v["variants"][-1]["url"]


class TwitterEntitySymbol(TwitterEntity):
    text: str


class TwitterEntityTimestamp(TwitterEntity):
    pass


class TwitterEntityUrl(TwitterEntity):
    display_url: str
    expanded_url: str
    url: str


class TwitterEntityUserMention(TwitterEntity):
    id: int = Field(alias="id_str")
    name: str
    screen_name: str


class TwitterEntities(BaseModel):
    hashtags: List[TwitterEntityHashTag] = []
    media: List[
        TwitterEntityMediaPhoto
        | TwitterEntityMediaVideo
        | TwitterEntityMediaAnimatedGif
    ] = []
    symbols: List[TwitterEntitySymbol] = []
    timestamps: List[TwitterEntityTimestamp] = []
    urls: List[TwitterEntityUrl] = []
    user_mentions: List[TwitterEntityUserMention] = []


class UserEntities(BaseModel):
    description: TwitterEntities
    url: TwitterEntities = TwitterEntities()


class TwitterUser(BaseModel):
    id: int
    name: str
    screen_name: str
    location: str
    description: str
    protected: Optional[bool] = None
    verified: bool
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    entities: UserEntities
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


class Tweet(BaseModel):
    id: int = Field(alias="id_str")
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    full_text: str
    display_text_range: List[int]
    lang: str
    possibly_sensitive: bool = False
    entities: TwitterEntities
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
                    if entry["entryId"].startswith("tweet-"):
                        if not base_tweet.conversation_threads:
                            base_tweet.conversation_threads.append([])
                        base_tweet.conversation_threads[0].extend(cls.from_entry(entry))
                    if entry["entryId"].startswith("conversationthread-"):
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
