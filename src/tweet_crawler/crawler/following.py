import asyncio
import json
import re
from typing import Final

from playwright.async_api import Page

from .followers import TwitterFollowersCrawler

FOLLOWING_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://(?:twitter|x)\.com/i/api/graphql/[^/]+/Following(\?.*)?$"
)


class TwitterFollowingCrawler(TwitterFollowersCrawler):
    def __init__(self, page: Page, screen_name: str):
        super().__init__(page, screen_name)
        self.page = page
        self.screen_name = screen_name
        self.url = f"https://x.com/{screen_name}/following"
        self.error_url = f"https://x.com/{screen_name}"
        self.done = asyncio.Event()
        self.exception_signal = asyncio.Event()

    async def handle_response(self, response):
        if FOLLOWING_PATTERN.match(response.url):
            try:
                response_body = await response.body()
                self.content = json.loads(response_body)
            finally:
                self.done.set()
