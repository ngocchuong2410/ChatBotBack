import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import time
from urllib.parse import urljoin

from chatbotAPI.Utils import get_es_client, logger


def main():
    print("Hello CRAWLER")
    es = get_es_client()
    logger.info(es.info())


if __name__ == "__main__":
    main()