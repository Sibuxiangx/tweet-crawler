import asyncio
import json
import re
from typing import AsyncGenerator, Final

from playwright.async_api import Page

from ..exception import NotAuthenticated
from ..model import TwitterUser

FOLLOWERS_PATTERN: Final[re.Pattern] = re.compile(
    r"^https://(?:twitter|x)\.com/i/api/graphql/[^/]+/Followers(\?.*)?$"
)


class TwitterFollowersCrawler:
    done: asyncio.Event
    exception_signal: asyncio.Event
    exception: Exception
    content: dict
    screen_name: str
    url: str
    error_url: str
    page: Page

    def __init__(self, page: Page, screen_name: str):
        self.page = page
        self.screen_name = screen_name
        self.url = f"https://x.com/{screen_name}/followers"
        self.error_url = f"https://x.com/{screen_name}"
        self.done = asyncio.Event()
        self.exception_signal = asyncio.Event()

    async def handle_redirection(self, frame):
        if frame.url == self.error_url:
            self.exception_signal.set()
            self.exception = NotAuthenticated(self.screen_name)
            self.done.set()

    async def handle_response(self, response):
        if FOLLOWERS_PATTERN.match(response.url):
            try:
                response_body = await response.body()
                self.content = json.loads(response_body)
            finally:
                self.done.set()

    async def run_yield(self) -> AsyncGenerator[list[TwitterUser], None]:
        terminate = False
        while not terminate:
            while not self.done.is_set():
                await self.page.keyboard.press("End")
            if self.exception_signal.is_set():
                raise self.exception
            self.done.clear()
            for ins in self.content["data"]["user"]["result"]["timeline"]["timeline"][
                "instructions"
            ]:
                if (
                    ins["type"] == "TimelineTerminateTimeline"
                    and ins["direction"] == "Bottom"
                ):
                    terminate = True
                if ins["type"] == "TimelineAddEntries":
                    users = [
                        TwitterUser.from_result(
                            entry["content"]["itemContent"]["user_results"]["result"]
                        )
                        for entry in ins["entries"]
                        if entry["content"]["entryType"] == "TimelineTimelineItem"
                    ]
                    yield users

    async def run(self) -> list[TwitterUser]:
        self.page.on("response", self.handle_response)
        self.page.on("framenavigated", self.handle_redirection)
        await self.page.goto(self.url)
        result: list[TwitterUser] = []
        async for users in self.run_yield():
            result.extend(users)
        return result
