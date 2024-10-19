import os
import unittest

from dotenv import load_dotenv
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from tweet_crawler import TwitterFollowingCrawler
from tweet_crawler.exception import NotAuthenticated

load_dotenv()


class FollowingCase(unittest.IsolatedAsyncioTestCase):
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page

    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def asyncTearDown(self):
        await self.page.close()
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def new_context(self, auth: bool):
        await self.page.close()
        await self.context.close()
        self.context = await self.browser.new_context()
        if auth:
            await self.context.add_cookies(
                [
                    {
                        "name": "auth_multi",
                        "value": os.environ["AUTH_MULTI"],
                        "domain": ".x.com",
                        "path": "/",
                        "expires": float(os.environ["AUTH_MULTI_EXPIRES"]),
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax",
                    },
                    {
                        "name": "auth_token",
                        "value": os.environ["AUTH_TOKEN"],
                        "domain": ".x.com",
                        "path": "/",
                        "expires": float(os.environ["AUTH_TOKEN_EXPIRES"]),
                        "httpOnly": True,
                        "sameSite": "None",
                        "secure": True,
                    },
                    {
                        "name": "ct0",
                        "value": os.environ["CT0"],
                        "domain": ".x.com",
                        "path": "/",
                        "expires": float(os.environ["CT0_EXPIRES"]),
                        "httpOnly": False,
                        "sameSite": "Lax",
                        "secure": True,
                    },
                ]
            )
        self.page = await self.context.new_page()

    async def test_not_authenticated(self):
        await self.new_context(auth=False)
        with self.assertRaises(NotAuthenticated):
            crawler = TwitterFollowingCrawler(
                self.page, os.environ["TWITTER_SCREEN_NAME"]
            )
            await crawler.run()

    async def test_authenticated(self):
        await self.new_context(auth=True)
        crawler = TwitterFollowingCrawler(self.page, os.environ["TWITTER_SCREEN_NAME"])
        result = await crawler.run()
        print("==========")
        print(f"{len(result)=}")
        for index, user in enumerate(result[:10]):
            print(f"{index + 1}. {user.id=} ({user.handle})")


if __name__ == "__main__":
    unittest.main()
