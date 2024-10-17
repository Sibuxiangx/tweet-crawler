import os
import unittest

from dotenv import load_dotenv
from playwright.async_api import Browser, Playwright, async_playwright

from tweet_crawler.crawler import TweetCrawler

load_dotenv()


class CrawlerCase(unittest.IsolatedAsyncioTestCase):
    playwright: Playwright
    browser: Browser

    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def asyncTearDown(self):
        await self.browser.close()
        await self.playwright.stop()

    async def test_plain_text(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_PLAIN_TEXT"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        print(f"{result.full_text=}")
        print(f"{result.text=}")
        await context.close()

    async def test_tweet_animated_gif(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_ANIMATED_GIF"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertIsNotNone(
            next(
                filter(lambda x: x.type == "animated_gif", result.entities.media), None
            )
        )
        print(f"{result.entities.media=}")
        await context.close()

    async def test_tweet_video(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_VIDEO"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "video", result.entities.media), None)
        )
        print(f"{result.entities.media=}")
        await context.close()

    async def test_tweet_photo(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_PHOTO"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "photo", result.entities.media), None)
        )
        print(f"{result.entities.media=}")
        await context.close()

    async def test_tweet_hashtag(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_HASHTAG"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertTrue(result.entities.hashtags)
        print(f"{result.entities.hashtags=}")
        await context.close()

    async def test_tweet_symbol(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_SYMBOL"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertTrue(result.entities.symbols)
        print(f"{result.entities.symbols=}")
        await context.close()

    async def test_tweet_url(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_URL"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertTrue(result.entities.urls)
        print(f"{result.entities.urls=}")
        await context.close()

    async def test_tweet_user_mention(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_USER_MENTION"]
        crawler = TweetCrawler(context, url)
        result = await crawler.run_and_parse()
        assert result
        self.assertTrue(result.entities.user_mentions)
        print(f"{result.entities.user_mentions=}")
        await context.close()

    async def test_authenticated(self):
        context = await self.browser.new_context()
        url = os.environ["TWEET_WITH_REPLY"]
        crawler = TweetCrawler(context, url)
        await crawler.add_cookies(
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
        result = await crawler.run_and_parse()
        assert result
        self.assertIsNotNone(result.conversation_threads)
        for index, thread in enumerate(result.conversation_threads):
            print("==========")
            print(f"{index + 1}. {thread.id=} ({thread.user.handle})")
            print(f"{thread.user.profile_image_url=}")
            print(f"{thread.full_text=}")
            print(f"{thread.text=}")
        await context.close()


if __name__ == "__main__":
    unittest.main()
