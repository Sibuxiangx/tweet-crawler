from datetime import datetime
from typing import List

from .model import (
    Tweet,
    TweetEntities,
    TweetEntityHashTag,
    TweetEntityMedia,
    TweetEntitySymbol,
    TweetEntityTimestamp,
    TweetEntityUrl,
    TweetEntityUserMention,
    TweetStatistics,
    TweetStatus,
    TweetUser,
    TweetUserStatistics,
    TweetUserStatus,
)


def parse_full(content: dict) -> Tweet:
    ins = content["data"]["threaded_conversation_with_injections_v2"]["instructions"]
    valid_ins = next(filter(lambda x: x["type"] == "TimelineAddEntries", ins))
    tweet = parse_tweet(
        valid_ins["entries"].pop(0)["content"]["itemContent"]["tweet_results"]["result"]
    )
    for entry in valid_ins["entries"]:
        if entry["content"]["entryType"] == "TimelineTimelineModule":
            tweet.conversation_threads.append(
                parse_tweet(
                    entry["content"]["items"][0]["item"]["itemContent"][
                        "tweet_results"
                    ]["result"]
                )
            )
    return tweet


def parse_guest(content: dict) -> Tweet:
    return parse_tweet(content["data"]["tweetResult"]["result"])


def parse_entity_hashtag(content: List[dict]) -> List[TweetEntityHashTag]:
    return [
        TweetEntityHashTag(
            indices=entity["indices"],
            text=entity["text"],
        )
        for entity in content
    ]


def parse_entity_media(content: List[dict]) -> List[TweetEntityMedia]:
    result = []
    for entity in content:
        if entity["type"] == "photo":
            result.append(
                TweetEntityMedia(
                    type="photo",
                    indices=entity["indices"],
                    url=entity["media_url_https"],
                    expanded_url=entity["expanded_url"],
                )
            )
        elif entity["type"] == "video":
            result.append(
                TweetEntityMedia(
                    type="video",
                    indices=entity["indices"],
                    url=entity["video_info"]["variants"][-1]["url"],
                    expanded_url=entity["expanded_url"],
                )
            )
        elif entity["type"] == "animated_gif":
            result.append(
                TweetEntityMedia(
                    type="animated_gif",
                    indices=entity["indices"],
                    url=entity["video_info"]["variants"][-1]["url"],
                    expanded_url=entity["expanded_url"],
                )
            )
    return result


def parse_entity_symbol(content: List[dict]) -> List[TweetEntitySymbol]:
    return [
        TweetEntitySymbol(
            indices=entity["indices"],
            text=entity["text"],
        )
        for entity in content
    ]


def parse_entity_timestamp(content: List[dict]) -> List[TweetEntityTimestamp]:
    return [
        TweetEntityTimestamp(
            indices=entity["indices"],
        )
        for entity in content
    ]


def parse_entity_url(content: List[dict]) -> List[TweetEntityUrl]:
    return [
        TweetEntityUrl(
            indices=entity["indices"],
            display_url=entity["display_url"],
            expanded_url=entity["expanded_url"],
            url=entity["url"],
        )
        for entity in content
    ]


def parse_entity_user_mention(content: List[dict]) -> List[TweetEntityUserMention]:
    return [
        TweetEntityUserMention(
            id=int(entity["id_str"]),
            name=entity["name"],
            screen_name=entity["screen_name"],
            indices=entity["indices"],
        )
        for entity in content
    ]


def parse_tweet(tweet_result: dict) -> Tweet:
    tweet_legacy = tweet_result["legacy"]
    user_result = tweet_result["core"]["user_results"]["result"]
    user_legacy = user_result["legacy"]
    tweet = Tweet(
        id=tweet_legacy["id_str"],
        created_at=datetime.strptime(
            tweet_legacy["created_at"], "%a %b %d %H:%M:%S %z %Y"
        ),
        full_text=tweet_legacy["full_text"],
        display_text_range=tweet_legacy["display_text_range"],
        lang=tweet_legacy["lang"],
        possibly_sensitive=tweet_legacy.get("possibly_sensitive", None),
        statistics=TweetStatistics(
            views_count=tweet_result["views"]["count"],
            bookmark_count=tweet_legacy["bookmark_count"],
            favourite_count=tweet_legacy["favorite_count"],
            quote_count=tweet_legacy["quote_count"],
            reply_count=tweet_legacy["reply_count"],
            retweet_count=tweet_legacy["retweet_count"],
        ),
        status=TweetStatus(
            bookmarked=tweet_legacy["bookmarked"],
            favourited=tweet_legacy["favorited"],
            retweeted=tweet_legacy["retweeted"],
        ),
        entities=TweetEntities(
            hashtags=parse_entity_hashtag(tweet_legacy["entities"].get("hashtags", [])),
            media=parse_entity_media(tweet_legacy["entities"].get("media", [])),
            symbols=parse_entity_symbol(tweet_legacy["entities"].get("symbols", [])),
            timestamps=parse_entity_timestamp(
                tweet_legacy["entities"].get("timestamps", [])
            ),
            urls=parse_entity_url(tweet_legacy["entities"].get("urls", [])),
            user_mentions=parse_entity_user_mention(
                tweet_legacy["entities"].get("user_mentions", [])
            ),
        ),
        conversation_threads=[],
        user=TweetUser(
            id=user_result["rest_id"],
            name=user_legacy["name"],
            screen_name=user_legacy["screen_name"],
            location=user_legacy["location"],
            description=user_legacy["description"],
            protected=user_legacy.get("protected", False),
            verified=user_legacy["verified"],
            created_at=datetime.strptime(
                user_legacy["created_at"], "%a %b %d %H:%M:%S %z %Y"
            ),
            statistics=TweetUserStatistics(
                followers_count=user_legacy["followers_count"],
                friends_count=user_legacy["friends_count"],
                listed_count=user_legacy["listed_count"],
                favourites_count=user_legacy["favourites_count"],
                statuses_count=user_legacy["statuses_count"],
            ),
            status=TweetUserStatus(
                followed_by=user_legacy.get("followed_by", None),
                following=user_legacy.get("following", None),
                can_dm=user_legacy.get("can_dm", None),
            ),
            pinned_tweet_ids=list(map(int, user_legacy["pinned_tweet_ids_str"])),
            profile_image=user_legacy["profile_image_url_https"].replace("_normal", ""),
            profile_banner=user_legacy.get("profile_banner_url", None),
        ),
    )
    return tweet
