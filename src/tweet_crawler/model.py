from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional


@dataclass
class TweetUserStatistics:
    followers_count: int
    friends_count: int
    listed_count: int
    favourites_count: int
    statuses_count: int


@dataclass
class TweetUserStatus:
    followed_by: Optional[bool]
    following: Optional[bool]
    can_dm: Optional[bool]


@dataclass
class TweetUser:
    id: int
    name: str
    screen_name: str
    location: str
    description: str
    protected: bool
    verified: bool
    created_at: datetime
    statistics: TweetUserStatistics
    status: TweetUserStatus
    pinned_tweet_ids: List[int]
    profile_image: str
    profile_banner: Optional[str]

    @property
    def handle(self):
        return f"@{self.screen_name}"


@dataclass
class TweetStatistics:
    views_count: int
    bookmark_count: int
    favourite_count: int
    quote_count: int
    reply_count: int
    retweet_count: int


@dataclass
class TweetStatus:
    bookmarked: bool
    favourited: bool  # noqa
    retweeted: bool


@dataclass
class TweetEntityHashTag:
    indices: List[int]
    text: str


@dataclass
class TweetEntityMedia:
    type: Literal["photo", "video", "animated_gif"]
    indices: List[int]
    url: str
    expanded_url: str


@dataclass
class TweetEntitySymbol:
    indices: List[int]
    text: str


@dataclass
class TweetEntityTimestamp:
    indices: List[int]


@dataclass
class TweetEntityUrl:
    indices: List[int]
    display_url: str
    expanded_url: str
    url: str


@dataclass
class TweetEntityUserMention:
    id: int
    name: str
    screen_name: str
    indices: List[int]


@dataclass
class TweetEntities:
    hashtags: List[TweetEntityHashTag]
    media: List[TweetEntityMedia]
    symbols: List[TweetEntitySymbol]
    timestamps: List[TweetEntityTimestamp]
    urls: List[TweetEntityUrl]
    user_mentions: List[TweetEntityUserMention]


@dataclass
class Tweet:
    id: int
    created_at: datetime
    full_text: str
    display_text_range: List[int]
    lang: str
    possibly_sensitive: Optional[bool]
    statistics: TweetStatistics
    status: TweetStatus
    entities: TweetEntities
    conversation_threads: List["Tweet"]
    user: TweetUser

    @property
    def text(self) -> str:
        return self.full_text[self.display_text_range[0] : self.display_text_range[1]]
