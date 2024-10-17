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

from tweet_crawler import TwitterStatusCrawler

load_dotenv()


class StatusCase(unittest.IsolatedAsyncioTestCase):
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

    async def test_plain_text(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_PLAIN_TEXT"])
        result = await crawler.run()
        print("==========")
        print(f"{result.full_text=}")
        print(f"{result.text=}")

    async def test_tweet_animated_gif(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_ANIMATED_GIF"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(
                filter(lambda x: x.type == "animated_gif", result.entities.media), None
            )
        )
        print("==========")
        print(f"{result.entities.media=}")

    async def test_tweet_video(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_VIDEO"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "video", result.entities.media), None)
        )
        print("==========")
        print(f"{result.entities.media=}")

    async def test_tweet_photo(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_PHOTO"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "photo", result.entities.media), None)
        )
        print("==========")
        print(f"{result.entities.media=}")

    async def test_tweet_hashtag(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_HASHTAG"])
        result = await crawler.run()
        self.assertTrue(result.entities.hashtags)
        print("==========")
        print(f"{result.entities.hashtags=}")

    async def test_tweet_symbol(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_SYMBOL"])
        result = await crawler.run()
        self.assertTrue(result.entities.symbols)
        print("==========")
        print(f"{result.entities.symbols=}")

    async def test_tweet_url(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_URL"])
        result = await crawler.run()
        self.assertTrue(result.entities.urls)
        print("==========")
        print(f"{result.entities.urls=}")

    async def test_tweet_user_mention(self):
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_USER_MENTION"])
        result = await crawler.run()
        self.assertTrue(result.entities.user_mentions)
        print("==========")
        print(f"{result.entities.user_mentions=}")

    async def test_authenticated(self):
        context = await self.browser.new_context()
        await context.add_cookies(
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
        page = await context.new_page()
        try:
            url = os.environ["TWEET_WITH_REPLY"]
            crawler = TwitterStatusCrawler(page, url)
            result = await crawler.run()
            self.assertIsNotNone(result.conversation_threads)
            for index, thread in enumerate(result.conversation_threads):
                print("==========")
                print(f"{index + 1}. {thread.id=} ({thread.user.handle})")
                print(f"{thread.user.profile_image_url=}")
                print(f"{thread.full_text=}")
                print(f"{thread.text=}")
        finally:
            await page.close()
            await context.close()


if __name__ == "__main__":
    unittest.main()
