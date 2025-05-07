# Tạo thư mục logs nếu chưa tồn tại
import logging
import os
import sys

from elasticsearch import Elasticsearch

os.makedirs("logs", exist_ok=True)

# Tạo logger toàn cục
logger = logging.getLogger("comestic_crawler_app_logger")
logger.setLevel(logging.DEBUG)  # Ghi cả DEBUG trở lên

# Định dạng log
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 🧾 File handler
file_handler = logging.FileHandler("logs/chatbotAPI.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 🖥 Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Có thể set INFO nếu không muốn quá nhiều log debug trên console
console_handler.setFormatter(formatter)

# Gắn handlers nếu chưa gắn
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)



# === Read config from .env ===
host = os.getenv("ELASTICSEARCH_HOST", "http://localhost")
port = os.getenv("ELASTICSEARCH_PORT", "9200")
user = os.getenv("ELASTICSEARCH_USER", None)
password = os.getenv("ELASTICSEARCH_PASSWORD", None)

# === Build connection URL ===
es_url = f"{host}:{port}"

# === Initialize Elasticsearch client ===
es_kwargs = {
    "hosts": [es_url],
    "request_timeout": 10,
    "max_retries": 3,
    "retry_on_timeout": True
}
if user and password:
    es_kwargs["basic_auth"] = (user, password)

_es_client = Elasticsearch(**es_kwargs)

if _es_client.ping():
    logger.info(f" Elasticsearch connected: {es_url}")
else:
    logger.warning("️ Elasticsearch is not responding!")

# === Hàm lấy client ===
def get_es_client():
    return _es_client