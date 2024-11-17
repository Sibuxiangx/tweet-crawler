import json
import re
from typing import Final

from playwright.async_api import Frame

from ..exception import TweetUnavailable
from ..model import Tweet, TweetTombstone
from ._base import StaticCrawler

TWEET_DETAIL_PATTERN: Final[re.Pattern] = re.compile(
    r"^https?://(?:twitter|x)\.com/i/api/graphql/[^/]+/TweetDetail(\?.*)?$"
)
TWEET_BY_ID_PATTERN: Final[re.Pattern] = re.compile(
    r"^https?://api\.(?:twitter|x)\.com/graphql/[^/]+/TweetResultByRestId(\?.*)?$"
)


class TwitterStatusCrawler(StaticCrawler[Tweet]):
    async def handle_redirection(self, frame: Frame) -> None:
        pass

    async def handle_response(self, response) -> None:
        if TWEET_DETAIL_PATTERN.match(response.url) or TWEET_BY_ID_PATTERN.match(
            response.url
        ):
            try:
                await self.parse(json.loads(await response.body()))
            except Exception as e:  # pragma: no cover
                self.exception = e
                self.exception_signal.set()
            finally:
                self.done_signal.set()

    async def parse(self, content: dict) -> None:
        data = content["data"]

        if "tweetResult" in data:
            result = data["tweetResult"]["result"]
            if result["__typename"] == "TweetUnavailable":
                self.exception = TweetUnavailable(result["reason"])
                self.exception_signal.set()
                return
            else:
                tweet_result = data["tweetResult"]["result"]
                parsed = Tweet.from_result(
                    tweet_result, rest_id=tweet_result["rest_id"]
                )
        elif "threaded_conversation_with_injections_v2" in data:
            parsed = Tweet.from_instructions(
                data["threaded_conversation_with_injections_v2"]["instructions"]
            )
        else:  # pragma: no cover
            raise ValueError("Invalid tweet data")

        if isinstance(parsed, TweetTombstone):
            self.exception = TweetUnavailable(parsed.text)
            self.exception_signal.set()
        else:
            self.result = parsed
