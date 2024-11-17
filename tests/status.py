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

from tweet_crawler import TwitterStatusCrawler
from tweet_crawler.exception import TweetUnavailable
from tweet_crawler.model import TweetTombstone

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
        await add_cookies(self.context)
        self.page = await self.context.new_page()

    async def asyncTearDown(self):
        await self.page.close()
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def test_plain_text(self):
        print("\n===== test_plain_text =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_PLAIN_TEXT"])
        result = await crawler.run()
        print(f"{result.full_text=}")
        print(f"{result.text=}")
        print("===== done =====")

    async def test_tweet_animated_gif(self):
        print("\n===== test_tweet_animated_gif =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_ANIMATED_GIF"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(
                filter(lambda x: x.type == "animated_gif", result.entities.media), None
            )
        )
        print(f"{result.entities.media=}")
        print("===== done =====")

    async def test_tweet_video(self):
        print("\n===== test_tweet_video =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_VIDEO"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "video", result.entities.media), None)
        )
        print(f"{result.entities.media=}")
        print("===== done =====")

    async def test_tweet_photo(self):
        print("\n===== test_tweet_photo =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_PHOTO"])
        result = await crawler.run()
        self.assertIsNotNone(
            next(filter(lambda x: x.type == "photo", result.entities.media), None)
        )
        print(f"{result.entities.media=}")
        print("===== done =====")

    async def test_tweet_hashtag(self):
        print("\n===== test_tweet_hashtag =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_HASHTAG"])
        result = await crawler.run()
        self.assertTrue(result.entities.hashtags)
        print(f"{result.entities.hashtags=}")
        print("===== done =====")

    async def test_tweet_symbol(self):
        print("\n===== test_tweet_symbol =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_SYMBOL"])
        result = await crawler.run()
        self.assertTrue(result.entities.symbols)
        print(f"{result.entities.symbols=}")
        print("===== done =====")

    async def test_tweet_url(self):
        print("\n===== test_tweet_url =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_URL"])
        result = await crawler.run()
        self.assertTrue(result.entities.urls)
        print(f"{result.entities.urls=}")
        print("===== done =====")

    async def test_tweet_user_mention(self):
        print("\n===== test_tweet_user_mention =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_USER_MENTION"])
        result = await crawler.run()
        self.assertTrue(result.entities.user_mentions)
        print(f"{result.entities.user_mentions=}")
        print("===== done =====")

    async def test_tweet_unavailable(self):
        print("\n===== test_tweet_unavailable =====")
        await self.context.clear_cookies()
        with self.assertRaises(TweetUnavailable):
            crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_NSFW"])
            await crawler.run()
        await add_cookies(self.context)
        print("===== done =====")

    async def test_guest(self):
        print("\n===== test_guest =====")
        await self.context.clear_cookies()
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_PLAIN_TEXT"])
        result = await crawler.run()
        print(f"{result.full_text=}")
        print(f"{result.text=}")
        await add_cookies(self.context)
        print("===== done =====")

    async def test_authenticated(self):
        print("\n===== test_authenticated =====")
        await add_cookies(self.context)
        url = os.environ["TWEET_WITH_REPLY"]
        crawler = TwitterStatusCrawler(self.page, url)
        result = await crawler.run()
        self.assertIsNotNone(result.conversation_threads)
        for index, thread in enumerate(result.conversation_threads):
            threaded = thread[0]
            if isinstance(threaded, TweetTombstone):  # pragma: no cover
                print(f"{index + 1}.\t[Tombstone] {threaded.text}")
                continue
            print(f"{index + 1}.\t{threaded.id=} ({threaded.user.handle})")
            print(f"\t{threaded.user.profile_image_url=}")
            print(f"\t{threaded.full_text=}")
            print(f"\t{threaded.text=}")
        print("===== done =====")

    async def test_tweet_with_visibility(self):
        print("\n===== test_tweet_with_visibility =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_WITH_VISIBILITY"])
        result = await crawler.run()
        print(f"{result.full_text=}")
        print(f"{result.text=}")
        print("===== done =====")

    async def test_tweet_main_tombstone(self):
        print("\n===== test_tweet_main_tombstone =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_MAIN_TOMBSTONE"])
        with self.assertRaises(TweetUnavailable):
            await crawler.run()
        print("===== done =====")

    async def test_tweet_thread_tombstone(self):
        print("\n===== test_tweet_thread_tombstone =====")
        crawler = TwitterStatusCrawler(self.page, os.environ["TWEET_THREAD_TOMBSTONE"])
        result = await crawler.run()
        has_tombstone = False
        for index, thread in enumerate(result.conversation_threads):
            for t_index, threaded in enumerate(thread):
                if isinstance(threaded, TweetTombstone):
                    has_tombstone = True
                    print(f"{index + 1}.{t_index}.\t[Tombstone] {threaded.text}")
                    break
        self.assertTrue(has_tombstone)
        print("===== done =====")


if __name__ == "__main__":
    unittest.main()
