import asyncio
from typing import AsyncGenerator, Generic, List, TypeVar

from playwright.async_api import Frame, Page, Response

_T = TypeVar("_T")


class CrawlerBase(Generic[_T]):
    done_signal: asyncio.Event

    exception_signal: asyncio.Event
    exception: Exception

    url: str
    page: Page

    def __init__(self, page: Page, url: str):
        self.done_signal = asyncio.Event()
        self.exception_signal = asyncio.Event()
        self.url = url
        self.page = page
        self.page.on("response", self.handle_response)
        self.page.on("framenavigated", self.handle_redirection)

    async def handle_redirection(self, frame: Frame) -> None:
        ...

    async def handle_response(self, response: Response) -> None:
        ...

    async def parse(self, content: dict) -> None:
        ...

    async def run(self) -> _T:
        ...


class StaticCrawler(CrawlerBase[_T]):
    result: _T

    async def run(self) -> _T:
        await self.page.goto(self.url)
        await self.done_signal.wait()
        if self.exception_signal.is_set():
            raise self.exception  # pragma: no cover
        return self.result


class ScrollableCrawler(CrawlerBase[List[_T]]):
    scroll_done_signal: asyncio.Event
    increment: List[_T]
    result: List[_T]

    def __init__(self, page: Page, url: str):
        super().__init__(page=page, url=url)
        self.scroll_done_signal = asyncio.Event()

    async def run_yield(self) -> AsyncGenerator[List[_T], None]:
        await self.page.goto(self.url)
        while not self.scroll_done_signal.is_set():
            while not self.done_signal.is_set():
                await self.page.keyboard.press("End")
            if self.exception_signal.is_set():
                raise self.exception
            self.done_signal.clear()
            yield self.increment

    async def run(self) -> List[_T]:
        self.result = []
        async for part in self.run_yield():
            self.result.extend(part)
        return self.result
