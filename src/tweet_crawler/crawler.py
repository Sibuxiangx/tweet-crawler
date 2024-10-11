import asyncio
import json
import re
from typing import Final, Optional, Sequence

from playwright._impl._api_structures import SetCookieParam  # noqa
from playwright.async_api import BrowserContext, Page

from .model import Tweet
from .parse import parse_full, parse_guest

TWEET_DETAIL_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://x\.com/i/api/graphql/[^/]+/TweetDetail(\?.*)?$"
)
TWEET_BY_ID_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://api\.x\.com/graphql/[^/]+/TweetResultByRestId(\?.*)?$"
)


class TweetCrawler:
    done: asyncio.Event
    full_content: Optional[dict]
    guest_content: Optional[dict]
    url: str

    context: BrowserContext
    page: Page

    def __init__(self, context: BrowserContext, url: str):
        self.context = context
        self.url = url
        self.done = asyncio.Event()
        self.full_content = None
        self.guest_content = None

    async def add_cookies(self, cookies: Sequence[SetCookieParam]):
        """
        Add cookies to the browser context

        Arguments:
            cookies {Sequence[SetCookieParam]} -- cookies to add, \
            `auth_multi` `auth_token` `ct0` is needed for authorization, \
            otherwise it will be treated as a guest
        """
        await self.context.add_cookies(cookies)

    async def handle_response(self, response):
        if TWEET_DETAIL_PATTERN.match(response.url):
            try:
                response_body = await response.body()
                self.full_content = json.loads(response_body)
            finally:
                self.done.set()
        elif TWEET_BY_ID_PATTERN.match(response.url):
            try:
                response_body = await response.body()
                self.guest_content = json.loads(response_body)
            finally:
                self.done.set()

    async def run(self) -> bool:
        self.page = await self.context.new_page()
        self.page.on("response", self.handle_response)
        await self.page.goto(self.url)
        await self.done.wait()
        await self.page.close()
        return (
            True
            if isinstance(self.full_content, dict)
            or isinstance(self.guest_content, dict)
            else False
        )

    def parse(self) -> Optional[Tweet]:
        return (
            parse_full(self.full_content)
            if isinstance(self.full_content, dict)
            else (
                parse_guest(self.guest_content)
                if isinstance(self.guest_content, dict)
                else None
            )
        )

    async def run_and_parse(self) -> Optional[Tweet]:
        await self.run()
        return self.parse()
