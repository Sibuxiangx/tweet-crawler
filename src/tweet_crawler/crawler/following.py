import json
import re
from typing import Final

from .followers import TwitterFollowersCrawler

FOLLOWING_PATTERN: Final[re.Pattern] = re.compile(
    r"^https?://(?:twitter|x)\.com/i/api/graphql/[^/]+/Following(\?.*)?$"
)


class TwitterFollowingCrawler(TwitterFollowersCrawler):
    URL_PATTERN: str = "https://x.com/{screen_name}/following"

    async def handle_response(self, response):
        if FOLLOWING_PATTERN.match(response.url):
            try:
                await self.parse(json.loads(await response.body()))
            finally:
                self.done_signal.set()
