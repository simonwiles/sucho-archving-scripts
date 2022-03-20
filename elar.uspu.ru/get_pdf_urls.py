#!/usr/bin/env python3

""" 
Script takes a list of D-SPACE records (?), fetches the pages, and returns all .pdf links
(This list is then supplied as a `seedFile` to `browsertrix-crawler` to force fetching
 the PDFs and combining with a previous crawl.)
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


# D-SPACE urls generated using the script at
#  https://github.com/Segerberg/SUCHO/blob/master/DSpace_OAI-PMH/dspace_ia.py
SOURCE_URLS_LIST = Path("elar-uspu-ru.dspace.urls")

BASE_URL = "http://elar.uspu.ru"

OUTPUT_PATH = Path("pdf_urls.txt")


async def check_url(session, url, i):
    logging.debug(colored("Checking %s", "yellow"), url)
    try:
        async with session.get(url) as response:
            logging.info(colored("%s : ok: %s", "green"), f"{i: >5}", url)
            response_text = await response.read()
            tree = fromstring(response_text.decode("utf-8"))
            pdf_urls = set(
                BASE_URL + a.get("href")
                for a in tree.xpath("//a[contains(@href, '.pdf')]")
            )
            return pdf_urls
        return pdf_urls
    except Exception as e:
        logging.info(colored("%s : %s error: %s", "red"), f"{i: >5}", url, e)
        return


async def check_urls(urls, output_stream):

    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, url in enumerate(urls):
            tasks.append(asyncio.ensure_future(check_url(session, url, i)))
            # await asyncio.sleep(0.5)

        extra_urls = await asyncio.gather(*tasks)

    for _extra_urls in (_ for _ in extra_urls if _ is not None):
        output_stream.write("\n".join(_extra_urls))


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
