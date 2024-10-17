from .model import Tweet


def parse_full(content: dict) -> Tweet:
    ins = content["data"]["threaded_conversation_with_injections_v2"]["instructions"]
    valid_ins = next(filter(lambda x: x["type"] == "TimelineAddEntries", ins))
    tweet = Tweet.from_result(
        valid_ins["entries"].pop(0)["content"]["itemContent"]["tweet_results"]["result"]
    )
    for entry in valid_ins["entries"]:
        if entry["content"]["entryType"] == "TimelineTimelineModule":
            tweet.conversation_threads.append(
                Tweet.from_result(
                    entry["content"]["items"][0]["item"]["itemContent"][
                        "tweet_results"
                    ]["result"]
                )
            )
    return tweet


def parse_guest(content: dict) -> Tweet:
    return Tweet.from_result(content["data"]["tweetResult"]["result"])
