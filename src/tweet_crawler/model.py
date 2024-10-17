from datetime import datetime
from typing import List, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class TweetUser(BaseModel):
    id: int
    name: str
    screen_name: str
    location: str
    description: str
    protected: Optional[bool] = None
    verified: bool
    created_at: datetime
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

    @field_validator("created_at", mode="before")  # noqa
    @classmethod
    def __validate_create_at(cls, v: str):
        return datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y")

    @property
    def handle(self):
        return f"@{self.screen_name}"

    @property
    def profile_image_url(self):
        return str(self.profile_image_url_normal).replace("_normal", "")

    @classmethod
    def from_result(cls, result: dict) -> "TweetUser":
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
    created_at: datetime
    full_text: str
    display_text_range: List[int]
    lang: str
    possibly_sensitive: bool = False
    entities: TweetEntities
    conversation_threads: List["Tweet"] = []
    user: TweetUser
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

    @field_validator("created_at", mode="before")  # noqa
    @classmethod
    def __validate_create_at(cls, v: str):
        return datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y")

    @classmethod
    def from_result(cls, result: dict) -> "Tweet":
        return cls.model_validate(
            result["legacy"]
            | {
                "views_count": result["views"]["count"],
                "user": TweetUser.from_result(result["core"]["user_results"]["result"]),
            }
        )
