from Utils import logger
from chatbotAPI.Utils import get_es_client


def main():
    logger.info("Hello ChatBotAPI")
    es = get_es_client()
    logger.info(es.info())


if __name__ == "__main__":
    main()