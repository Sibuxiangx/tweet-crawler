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
from util import add_cookies

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
        await add_cookies(self.context)
        self.page = await self.context.new_page()

    async def asyncTearDown(self):
        await self.page.close()
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def test_not_authenticated(self):
        print("\n===== test_not_authenticated =====")
        with self.assertRaises(NotAuthenticated):
            await self.context.clear_cookies()
            crawler = TwitterFollowingCrawler(
                self.page, os.environ["TWITTER_SCREEN_NAME"]
            )
            await crawler.run()
        await add_cookies(self.context)
        print("===== done =====")

    async def test_authenticated(self):
        print("\n===== test_authenticated =====")
        crawler = TwitterFollowingCrawler(self.page, os.environ["TWITTER_SCREEN_NAME"])
        result = await crawler.run()
        print(f"{len(result)=}")
        for index, user in enumerate(result[:10]):
            print(f"{index + 1}. {user.id=} ({user.handle})")
        print("===== done =====")


if __name__ == "__main__":
    unittest.main()
