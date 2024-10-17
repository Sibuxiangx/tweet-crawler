import asyncio
import json
import re
from typing import Final

from playwright.async_api import Page

from ..model import Tweet

TWEET_DETAIL_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://(?:twitter|x)\.com/i/api/graphql/[^/]+/TweetDetail(\?.*)?$"
)
TWEET_BY_ID_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://api\.(?:twitter|x)\.com/graphql/[^/]+/TweetResultByRestId(\?.*)?$"
)


class TwitterStatusCrawler:
    done: asyncio.Event
    content: dict
    url: str
    page: Page

    def __init__(self, page: Page, url: str):
        self.page = page
        self.url = url
        self.done = asyncio.Event()

    async def handle_response(self, response):
        if TWEET_DETAIL_PATTERN.match(response.url) or TWEET_BY_ID_PATTERN.match(
            response.url
        ):
            try:
                response_body = await response.body()
                self.content = json.loads(response_body)
            finally:
                self.done.set()

    async def run(self) -> Tweet:
        self.page.on("response", self.handle_response)
        await self.page.goto(self.url)
        await self.done.wait()
        if "tweetResult" in self.content["data"]:
            return Tweet.from_result(self.content["data"]["tweetResult"]["result"])
        ins = self.content["data"]["threaded_conversation_with_injections_v2"][
            "instructions"
        ]
        valid_ins = next(filter(lambda x: x["type"] == "TimelineAddEntries", ins))
        tweet = Tweet.from_result(
            valid_ins["entries"].pop(0)["content"]["itemContent"]["tweet_results"][
                "result"
            ]
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
