# Tweet Crawler

![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![Imports](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)
![GitHub License](https://img.shields.io/github/license/nullqwertyuiop/tweet-crawler)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fnullqwertyuiop%2Ftweet-crawler%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
[![Codecov](https://img.shields.io/codecov/c/github/nullqwertyuiop/tweet-crawler)](https://codecov.io/gh/nullqwertyuiop/tweet-crawler)

Tweet Crawler is a Python-based web scraping tool that leverages Playwright to intercept responses from Twitter and parse them into manipulable dataclasses. This project allows users to extract comprehensive tweet data either in guest mode or authenticated mode (via cookies).

## Features

- **Guest Mode**:
    - Fetch basic tweet details from a given status link without authentication.
    - Extract data such as tweet content, user details, media, and reaction statistics.

- **Authenticated Mode** (requires cookies):
    - Access additional tweet details including reply threads.
    - Provides a more extensive dataset by using user-specific cookie information.

## Installation

### Install as a VCS Dependency

Tweet Crawler can be installed as a VCS dependency in your project.

Here is how you can add it to your project using [PDM](https://pdm-project.org/):

1. **Install Dependencies**

   Ensure you have Python (version 3.10 or higher) installed and [PDM](https://pdm-project.org/). Then, run:

   ```bash
   pdm add "git+https://github.com/nullqwertyuiop/tweet-crawler.git@main"
   ```

2. **Set Up Playwright**

   Initialize Playwright by running:

   ```bash
   pdm run playwright install
   ```

### Clone directly from GitHub

1. **Clone the Repository**

   ```bash
   git clone https://github.com/nullqwertyuiop/tweet-crawler.git
   cd tweet-crawler
   ```

2. **Install Dependencies**

   Ensure you have Python (version 3.10 or higher) installed and [PDM](https://pdm-project.org/). Then, run:

   ```bash
   pdm install
   ```

3. **Set Up Playwright**

   Initialize Playwright by running:

   ```bash
   pdm run playwright install
   ```

## Usage

### Spinning Up an Async Playwright Instance

Tweet Crawler needs an instance of async playwright to interact with the browser.

Here's an example of how to create one:

```python
from playwright.async_api import async_playwright

url: str = ...  # URL of the tweet to crawl

async with async_playwright() as p:
    browser = await p.chromium.launch()
    context = await browser.new_context()
    page = await browser.new_page()
    crawler = TwitterStatusCrawler(page, url)
```

### Running in Guest Mode

To crawl tweets as a guest (without replies), simply run:

```python
await crawler.run()
```

### Running with Cookies

For fetching replies and extended information, you need to provide your Twitter cookies.

Here shows an example of how to add cookies to the crawler from environment variables:

> [!CAUTION]
> Never hardcode your cookies directly in the code. Doing so can expose your sensitive information.
> Use environment variables or a secure method to store them.

```python
context: BrowserContext

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
```

Then, you can run the crawler as usual:

```python
await crawler.run()
```

## Data Output

The data is parsed into Python dataclasses for easy handling and manipulation. The following information can be extracted:

- **Tweet Content**: The text of the tweet.
- **User Information**: Username and profile details of the tweet author.
- **Media**: Links to any media (images, videos, etc.) included in the tweet.
- **Statistics**: Number of likes, retweets, and other reaction metrics.
- **Replies**: (Authenticated mode only) Full threads of replies to the tweet.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests with improvements. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/YourFeature`)
3. Commit your Changes (`git commit -m 'Add some feature'`)
4. Push to the Branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is intended for educational and research purposes only. Please ensure you comply with Twitter's terms of service and any applicable laws before using this tool to scrape data from their platform. Use responsibly.
