import json
import re
from typing import Final

from playwright.async_api import Frame, Page, Response

from ..exception import NotAuthenticated
from ..model import TwitterUser
from ._base import ScrollableCrawler

FOLLOWERS_PATTERN: Final[re.Pattern] = re.compile(
    r"^https?://(?:twitter|x)\.com/i/api/graphql/[^/]+/Followers(\?.*)?$"
)


class TwitterFollowersCrawler(ScrollableCrawler[TwitterUser]):
    screen_name: str
    URL_PATTERN: str = "https://x.com/{screen_name}/followers"

    def __init__(self, page: Page, screen_name: str):
        super().__init__(
            page=page, url=self.URL_PATTERN.format(screen_name=screen_name)
        )
        self.screen_name = screen_name

    async def handle_redirection(self, frame: Frame) -> None:
        if frame.url == f"https://x.com/{self.screen_name}":
            self.exception_signal.set()
            self.exception = NotAuthenticated(self.screen_name)
            self.done_signal.set()

    async def handle_response(self, response: Response) -> None:
        if FOLLOWERS_PATTERN.match(response.url):
            try:
                await self.parse(json.loads(await response.body()))
            finally:
                self.done_signal.set()

    async def parse(self, content: dict) -> None:
        for ins in content["data"]["user"]["result"]["timeline"]["timeline"][
            "instructions"
        ]:
            if (
                ins["type"] == "TimelineTerminateTimeline"
                and ins["direction"] == "Bottom"
            ):
                self.scroll_done_signal.set()
            if ins["type"] == "TimelineAddEntries":
                users = [
                    TwitterUser.from_result(
                        entry["content"]["itemContent"]["user_results"]["result"]
                    )
                    for entry in ins["entries"]
                    if entry["content"]["entryType"] == "TimelineTimelineItem"
                ]
                self.increment = users
