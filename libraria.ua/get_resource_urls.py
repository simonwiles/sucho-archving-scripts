#!/usr/bin/env python3

"""
Script takes a list of URLs to libraria.ua "numbers" interfaces, fetches the pages, and
returns URLs for all the images and API calls necessary for a completely functional
interface.

(This list is then supplied as a `seedFile` to `browsertrix-crawler` to force fetching
 the these resources and combining with a previous crawl.)
"""

import asyncio
import logging
import sys
from pathlib import Path

import aiohttp
from lxml.html.soupparser import fromstring

try:
    assert sys.stdout.isatty()
    from termcolor import colored
except (AssertionError, ImportError):

    def colored(text, *args, **kwargs):
        """Dummy function to pass text through without escape codes if stdout is not a
        TTY or termcolor is not available."""
        return text


OUTPUT_PATH = Path("resource_urls.txt")

SOURCE_URLS_LIST = Path("numbers.urls")

BASE_URL = "https://libraria.ua"
PAGE_URL_TEMPLATE = "https://libraria.ua/page?get_page={page_id}"
ARTICLE_TEXT_URL_TEMPLATE = "https://libraria.ua/page?get_item=article&id={article_id}"
PICTURE_TEXT_URL_TEMPLATE = "https://libraria.ua/page?get_item=picture&id={picture_id}"


async def check_url(session, url, i):
    logging.debug(colored("Checking %s", "yellow"), url)
    try:
        async with session.get(url) as response:
            logging.info(colored("%s : ok: %s", "green"), f"{i: >5}", url)
            response_text = await response.read()
            tree = fromstring(response_text.decode("utf-8"))
            img_urls = [
                BASE_URL + img.get("src").replace("/small_images/", "/big_images/")
                for img in tree.xpath("//ul[@class='slidee']//img")
            ]
            page_urls = [
                PAGE_URL_TEMPLATE.format(page_id=li.get("data-page"))
                for li in tree.xpath("//ul[@class='slidee']//li")
            ]
            article_text_urls = [
                ARTICLE_TEXT_URL_TEMPLATE.format(article_id=a.get("data-article-id"))
                for a in tree.xpath("//a[@data-type='article']")
            ]
            picture_text_urls = [
                PICTURE_TEXT_URL_TEMPLATE.format(picture_id=a.get("data-picture-id"))
                for a in tree.xpath("//a[@data-type='picture']")
            ]
        return [*img_urls, *page_urls, *article_text_urls, *picture_text_urls]
    except Exception as e:
        logging.info(colored("%s : %s error: %s", "red"), f"{i: >5}", url, e)
        return


async def check_urls(urls, output_stream):

    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, url in enumerate(urls):
            tasks.append(asyncio.ensure_future(check_url(session, url, i)))
            await asyncio.sleep(0.1)

        extra_urls = await asyncio.gather(*tasks)

    for _extra_urls in (_ for _ in extra_urls if _ is not None):
        output_stream.write("\n".join(_extra_urls) + "\n")


def main():
    """Command-line entry-point."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with SOURCE_URLS_LIST.open("r", encoding="utf-8") as _fh:
        source_urls_list = (_.strip() for _ in _fh.readlines())

    with OUTPUT_PATH.open("w", encoding="utf8") as _fh:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(check_urls(source_urls_list, _fh))


if __name__ == "__main__":
    main()
