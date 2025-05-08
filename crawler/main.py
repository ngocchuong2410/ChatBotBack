import os

from crawler.core.logger_factory import get_logger
from crawler.repository.product_repository import ProductRepository
from crawler.service.incidecoder_crawler_service import IncidecoderCrawler


def main():
    logger = get_logger()
    product_repo = ProductRepository()
    base_url = os.getenv("URL_INCIDECODER")
    max_pages = os.getenv("MAX_PAGES")
    ic_crawler = IncidecoderCrawler(logger, product_repo, base_url)
    ic_crawler.run(max_pages)


if __name__ == "__main__":
    main()
