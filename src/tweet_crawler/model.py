from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, Field, model_validator
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
    url: AnyHttpUrl
    expanded_url: AnyHttpUrl
    thumbnail_url: AnyHttpUrl = Field(alias="media_url_https")
    height: int
    width: int
    duration_ms: int

    @model_validator(mode="before")  # noqa
    @classmethod
    def __preprocess_data(cls, v: dict) -> dict:
        if all(
            [
                variants := v.get("video_info", {}).get("variants"),
                height := v.get("original_info", {}).get("height"),
                width := v.get("original_info", {}).get("width"),
                duration_ms := v.get("video_info", {}).get("duration_millis"),
            ]
        ):
            v["url"] = variants[-1]["url"]
            v["height"] = height
            v["width"] = width
            v["duration_ms"] = duration_ms
        return v


class TwitterEntityMediaAnimatedGif(TwitterEntity):
    type: Literal["animated_gif"]
    url: AnyHttpUrl
    expanded_url: AnyHttpUrl
    thumbnail_url: AnyHttpUrl = Field(alias="media_url_https")
    height: int
    width: int

    @model_validator(mode="before")  # noqa
    @classmethod
    def __preprocess_data(cls, v: dict) -> dict:
        if all(
            [
                variants := v.get("video_info", {}).get("variants"),
                height := v.get("original_info", {}).get("height"),
                width := v.get("original_info", {}).get("width"),
            ]
        ):
            v["url"] = variants[-1]["url"]
            v["height"] = height
            v["width"] = width
        return v


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
    hashtags: List[TwitterEntityHashTag] = Field(default_factory=list)
    media: List[
        TwitterEntityMediaPhoto
        | TwitterEntityMediaVideo
        | TwitterEntityMediaAnimatedGif
    ] = Field(default_factory=list)
    symbols: List[TwitterEntitySymbol] = Field(default_factory=list)
    timestamps: List[TwitterEntityTimestamp] = Field(default_factory=list)
    urls: List[TwitterEntityUrl] = Field(default_factory=list)
    user_mentions: List[TwitterEntityUserMention] = Field(default_factory=list)


class UserEntities(BaseModel):
    description: TwitterEntities
    url: TwitterEntities = TwitterEntities()


class TwitterUser(BaseModel):
    id: int
    name: str
    screen_name: str
    location: Optional[str] = None
    description: str
    protected: Optional[bool] = None
    verified: bool
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    entities: UserEntities
    pinned_tweet_ids: List[int] = Field(default_factory=list)
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
        legacy_data = result.get("legacy", {})
        user_data = {
            "id": result.get("rest_id"),
            "name": legacy_data.get("name"),
            "screen_name": legacy_data.get("screen_name"),
            "description": legacy_data.get("description"),
            "protected": legacy_data.get("protected"),
            "verified": result.get("verification", {}).get("verified", False) if "verification" in result else legacy_data.get("verified", False), # Handle new and old structures
            "created_at": legacy_data.get("created_at"),
            "entities": legacy_data.get("entities", {}),
            "pinned_tweet_ids": legacy_data.get("pinned_tweet_ids_str", []),
            "profile_image_url_https": result.get("avatar", {}).get("image_url") if "avatar" in result else legacy_data.get("profile_image_url_https"), # Handle new and old structures
            "profile_banner_url": legacy_data.get("profile_banner_url"),
            "followers_count": legacy_data.get("followers_count"),
            "friends_count": legacy_data.get("friends_count"),
            "listed_count": legacy_data.get("listed_count"),
            "favourites_count": legacy_data.get("favourites_count"),
            "statuses_count": legacy_data.get("statuses_count"),
            "following": result.get("relationship_perspectives", {}).get("following"),
            "can_dm": result.get("dm_permissions", {}).get("can_dm"),
        }
        # Extract location
        location_data = result.get("location", {})
        if isinstance(location_data, dict) and "location" in location_data:
            user_data["location"] = location_data["location"]
        elif isinstance(location_data, str): # for legacy structure if any
             user_data["location"] = location_data
        else:
            user_data["location"] = legacy_data.get("location")


        # Filter out None values to allow Pydantic to use default_factory or defaults
        validated_data = {k: v for k, v in user_data.items() if v is not None or k in ['profile_banner_url', 'location', 'protected', 'followed_by', 'following', 'can_dm']}
        
        # Ensure entities is properly structured if it comes from legacy_data without sub-fields
        if 'entities' in validated_data and isinstance(validated_data['entities'], dict):
            if 'description' not in validated_data['entities']:
                validated_data['entities']['description'] = {"urls": []} # default empty structure
            if 'url' not in validated_data['entities'] and 'urls' in legacy_data.get('entities', {}).get('url', {}): # Check if 'url' itself has 'urls'
                 validated_data['entities']['url'] = legacy_data['entities']['url']
            elif 'url' not in validated_data['entities']:
                 validated_data['entities']['url'] = {"urls": []}


        return cls.model_validate(validated_data)


class TweetTombstone(BaseModel):
    id: int
    conversation_threads: List[List[Union["Tweet", "TweetTombstone"]]] = Field(
        default_factory=list
    )
    text: str


class Tweet(BaseModel):
    id: int = Field(alias="id_str")
    created_at: Annotated[datetime, BeforeValidator(_twitter_datetime)]
    full_text: str
    display_text_range: List[int]
    lang: str
    possibly_sensitive: bool = False
    entities: TwitterEntities
    conversation_threads: List[List[Union["Tweet", "TweetTombstone"]]] = Field(
        default_factory=list
    )
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
    def from_instructions(cls, result: List[dict]) -> Union["Tweet", "TweetTombstone"]:
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
    def from_entry(cls, result: dict) -> List[Union["Tweet", "TweetTombstone"]]:
        content = result["content"]
        if result["entryId"].startswith("tweet"):
            item = content["itemContent"]
            assert item["itemType"] == "TimelineTweet"
            return [
                cls.from_result(
                    item["tweet_results"]["result"],
                    rest_id=int(result["entryId"].split("-")[-1]),
                )
            ]
        else:
            return [
                cls.from_result(
                    item["item"]["itemContent"]["tweet_results"]["result"],
                    rest_id=int(item["entryId"].split("-")[-1]),
                )
                for item in content["items"]
                if "cursor" not in item["entryId"]
            ]

    @classmethod
    def from_result(
        cls, result: dict, rest_id: int
    ) -> Union["Tweet", "TweetTombstone"]:
        if result["__typename"] == "TweetTombstone":
            return TweetTombstone(id=rest_id, text=result["tombstone"]["text"]["text"])
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
