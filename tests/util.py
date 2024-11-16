import os

from playwright.async_api import BrowserContext


async def add_cookies(context: BrowserContext):
    await context.add_cookies(
        [
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
