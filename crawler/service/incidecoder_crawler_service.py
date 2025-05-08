import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from crawler.core.logger_factory import get_logger
from crawler.repository.product_repository import ProductRepository


class IncidecoderCrawler:
    def __init__(self, logger=None, product_repository: ProductRepository = None, base_url: "" = None):

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        self.product_repository = product_repository
        self.logger = logger or get_logger()

    def get_ingredient_urls(self, page=1, max_pages=10):
        """
        Lấy danh sách URL của các thành phần mỹ phẩm

        Args:
            page: Số trang bắt đầu
            max_pages: Số trang tối đa sẽ duyệt

        Returns:
            list: Danh sách các URL thành phần
        """
        ingredient_urls = []
        current_page = page

        while current_page <= max_pages:
            try:
                url = f"{self.base_url}/ingredients/page/{current_page}/"
                self.logger.info(f"Đang lấy danh sách thành phần từ trang {current_page}: {url}")

                response = self.session.get(url)
                if response.status_code != 200:
                    self.logger.warning(f"Không thể truy cập trang {url}, status code: {response.status_code}")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')

                # Tìm các liên kết đến trang thành phần
                ingredient_links = soup.select('.ingredient-list-container .ingred-link')

                if not ingredient_links:
                    self.logger.info(f"Không tìm thấy thêm thành phần nào ở trang {current_page}")
                    break

                for link in ingredient_links:
                    ingredient_url = urljoin(self.base_url, link['href'])
                    ingredient_urls.append(ingredient_url)

                self.logger.info(f"Đã tìm thấy {len(ingredient_links)} thành phần ở trang {current_page}")
                current_page += 1

                # Đợi để tránh bị chặn
                time.sleep(2)

            except Exception as e:
                self.logger.error(f"Lỗi khi crawl trang {current_page}: {str(e)}")
                break

        self.logger.info(f"Tổng cộng tìm thấy {len(ingredient_urls)} URL thành phần")
        return ingredient_urls

    def parse_ingredient_page(self, url):
        """
        Phân tích trang thành phần để lấy thông tin chi tiết

        Args:
            url: URL của trang thành phần

        Returns:
            dict: Dữ liệu thành phần đã được phân tích
        """
        self.logger.info(f"Đang phân tích trang: {url}")

        try:
            response = self.session.get(url)
            if response.status_code != 200:
                self.logger.warning(f"Không thể truy cập trang {url}, status code: {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Lấy thông tin cơ bản
            name = soup.select_one('h1.ingredient-title')
            name = name.text.strip() if name else "Unknown"

            # Lấy các tên khác (aliases)
            aliases_section = soup.select_one('.also-called')
            aliases = []
            if aliases_section:
                aliases_text = aliases_section.text.replace("Also-called:", "").strip()
                aliases = [alias.strip() for alias in aliases_text.split(',') if alias.strip()]

            # Lấy mức độ kích ứng và gây mụn
            irritancy = "Unknown"
            comedogenicity = "Unknown"

            irritancy_section = soup.select_one('.irritancy')
            if irritancy_section:
                irritancy_text = irritancy_section.text.strip()
                irritancy_match = re.search(r'irritancy: (\w+)', irritancy_text, re.IGNORECASE)
                if irritancy_match:
                    irritancy = irritancy_match.group(1)

            comedo_section = soup.select_one('.comedogenicity')
            if comedo_section:
                comedo_text = comedo_section.text.strip()
                comedo_match = re.search(r'comedogenicity: (\w+)', comedo_text, re.IGNORECASE)
                if comedo_match:
                    comedogenicity = comedo_match.group(1)

            # Lấy mô tả và chức năng
            description = ""
            what_it_does = ""

            description_section = soup.select_one('.ingredient-description')
            if description_section:
                description = description_section.text.strip()

            function_section = soup.select_one('.what-it-does')
            if function_section:
                what_it_does = function_section.text.replace("What-it-does:", "").strip()

            # Lấy mức độ nguy hại
            hazard_level = "Low"  # Mặc định
            ewg_rating = None

            ewg_section = soup.select_one('.ewg-rating')
            if ewg_section:
                ewg_text = ewg_section.text.strip()
                ewg_match = re.search(r'EWG rating: (\d+(?:\.\d+)?)', ewg_text)
                if ewg_match:
                    ewg_rating = float(ewg_match.group(1))
                    # Phân loại mức độ nguy hại dựa trên điểm EWG
                    if ewg_rating >= 7:
                        hazard_level = "High"
                    elif ewg_rating >= 3:
                        hazard_level = "Moderate"
                    else:
                        hazard_level = "Low"

            # Lấy chức năng
            functions = []
            functions_list = soup.select('.what-it-does .func-badge')
            if functions_list:
                functions = [func.text.strip() for func in functions_list]

            # Tạo đối tượng dữ liệu
            ingredient_data = {
                "name": name,
                "aliases": aliases,
                "what_it_does": what_it_does,
                "irritancy": irritancy,
                "comedogenicity": comedogenicity,
                "hazard_level": hazard_level,
                "ewg_rating": ewg_rating,
                "description": description,
                "functions": functions,
                "url": url,
                "last_updated": time.strftime('%Y-%m-%dT%H:%M:%S')
            }

            self.logger.info(f"Đã phân tích thành công thành phần: {name}")
            return ingredient_data

        except Exception as e:
            self.logger.error(f"Lỗi khi phân tích trang {url}: {str(e)}")
            return None

    def run(self, max_pages=10, batch_size=50):
        """
        Chạy crawler để thu thập và lưu dữ liệu

        Args:
            max_pages: Số trang tối đa sẽ duyệt
            batch_size: Số lượng thành phần xử lý mỗi lần trước khi lưu
        """
        self.logger.info(f"Bắt đầu quá trình crawler với {max_pages} trang")

        # Lấy danh sách URL thành phần
        ingredient_urls = self.get_ingredient_urls(max_pages=max_pages)

        # Xử lý từng URL theo lô
        data_batch = []
        for i, url in enumerate(ingredient_urls):
            ingredient_data = self.parse_ingredient_page(url)
            if ingredient_data:
                data_batch.append(ingredient_data)

            # Khi đạt đủ kích thước lô hoặc là URL cuối cùng, lưu vào Elasticsearch
            if len(data_batch) >= batch_size or i == len(ingredient_urls) - 1:
                self.product_repository.save_ingredients(data_batch)
                data_batch = []  # Xóa lô hiện tại

            # Đợi để tránh bị chặn
            time.sleep(1)

        self.logger.info("Hoàn thành quá trình crawler")
