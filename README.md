IncideCoder Scraper với Elasticsearch
Script này giúp thu thập dữ liệu về thành phần mỹ phẩm từ trang web IncideCoder.com và lưu vào cả file JSON và Elasticsearch để dễ dàng tìm kiếm và phân tích.
Yêu cầu
pip install requests beautifulsoup4 elasticsearch lxml
Cách sử dụng
Thu thập dữ liệu từ nhiều trang và lưu vào cả JSON và Elasticsearch
bashpython incidecoder_scraper_with_elasticsearch.py --pages 5 --output ingredients.json --es-host http://localhost:9200 --es-index cosmetic_ingredients
Thu thập dữ liệu từ một URL cụ thể
bashpython incidecoder_scraper_with_elasticsearch.py --single https://incidecoder.com/ingredients/niacinamide
Chỉ lưu vào Elasticsearch từ file JSON có sẵn (không thu thập dữ liệu mới)
bashpython incidecoder_scraper_with_elasticsearch.py --no-scrape --output ingredients.json
Chỉ thu thập dữ liệu và lưu vào JSON (không lưu vào Elasticsearch)
bashpython incidecoder_scraper_with_elasticsearch.py --pages 3 --no-es
Tham số

--pages: Số trang cần thu thập (mặc định: 3)
--output: Tên file JSON đầu ra (mặc định: ingredients_data.json)
--es-host: Địa chỉ máy chủ Elasticsearch (mặc định: http://localhost:9200)
--es-index: Tên index trong Elasticsearch (mặc định: ingredients)
--no-scrape: Bỏ qua việc thu thập dữ liệu, chỉ đọc từ file JSON
--no-es: Bỏ qua việc lưu vào Elasticsearch
--single: URL của một thành phần cụ thể cần thu thập

Dữ liệu được thu thập

Tên thành phần
Bí danh (aliases)
Chức năng (what_it_does, functions)
Mức độ kích ứng (irritancy)
Mức độ gây mụn (comedogenicity)
Đánh giá EWG (ewg_rating)
Mức độ nguy hiểm (hazard_level)
Mô tả chi tiết (description)
URL
Ngày thu thập dữ liệu (scrape_date)

Tìm kiếm trong Elasticsearch
Sau khi dữ liệu được đưa vào Elasticsearch, bạn có thể tìm kiếm như sau:
Tìm theo tên:
GET /ingredients/_search
{
  "query": {
    "match": {
      "name": "niacinamide"
    }
  }
}
Tìm theo chức năng:
GET /ingredients/_search
{
  "query": {
    "match": {
      "functions": "moisturizer"
    }
  }
}
Tìm theo mức độ kích ứng:
GET /ingredients/_search
{
  "query": {
    "term": {
      "irritancy": "0"
    }
  }
}