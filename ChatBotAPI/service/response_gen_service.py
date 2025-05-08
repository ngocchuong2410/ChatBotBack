"""
Mô-đun tạo câu trả lời sử dụng Jinja2 template engine
"""
import os
from typing import Dict, List, Any

from jinja2 import Environment, FileSystemLoader, BaseLoader, select_autoescape


class ResponseGenerator:
    """
    Lớp tạo câu trả lời sử dụng Jinja2 template engine
    """

    def __init__(self, templates_dir: str = None):
        """
        Khởi tạo response generator với Jinja2

        Args:
            templates_dir: Thư mục chứa các template (tùy chọn)
        """
        # Nếu có thư mục template, sử dụng FileSystemLoader
        if templates_dir and os.path.exists(templates_dir):
            self.env = Environment(
                loader=FileSystemLoader(templates_dir),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
        # Nếu không, sử dụng các template được định nghĩa sẵn
        else:
            self.env = Environment(
                loader=BaseLoader(),
                trim_blocks=True,
                lstrip_blocks=True
            )
            # Đăng ký các template trực tiếp
            self._register_templates()

        # Đăng ký các filter tùy chỉnh
        self.env.filters['get_hazard_emoji'] = self._get_hazard_emoji

    def _get_hazard_emoji(self, hazard_level: str) -> str:
        """
        Trả về emoji tương ứng với mức độ nguy hại

        Args:
            hazard_level: Mức độ nguy hại

        Returns:
            Emoji tương ứng
        """
        if not hazard_level:
            return "❓"

        hazard_level = hazard_level.lower()

        if hazard_level in ["an toàn", "low", "thấp"]:
            return "🟢"
        elif hazard_level in ["trung bình", "medium"]:
            return "🟠"
        else:
            return "🔴"

    def _register_templates(self):
        """
        Đăng ký các template mặc định
        """
        # Template cho trường hợp không tìm thấy thành phần
        self.env.from_string(
            "Tôi không tìm thấy thông tin về thành phần mỹ phẩm trong câu hỏi của bạn. "
            "Vui lòng cung cấp tên cụ thể của thành phần mỹ phẩm bạn muốn tìm hiểu.",
        )

        # Template cho thông tin chung về thành phần
        self.env.from_string("""
{%- if ingredients_data %}
Tôi đã tìm thấy thông tin về {{ ingredients_data|length }} thành phần mỹ phẩm:

{% for ingredient in ingredients_data %}
{{ loop.index }}. {{ ingredient.hazard_level|get_hazard_emoji }} {{ ingredient.name }} (Mức độ nguy hại: {{ ingredient.hazard_level }})
   {{ ingredient.description }}
{%- if ingredient.effects and ingredient.effects|length > 0 %}
   Tác động tiềm ẩn: {{ ingredient.effects|join(', ') }}
{%- endif %}

{% endfor %}
{%- endif %}

Lưu ý: Thông tin trên chỉ mang tính tham khảo. Mỗi người có thể phản ứng khác nhau với các thành phần mỹ phẩm. Nếu bạn có làn da nhạy cảm, hãy tham khảo ý kiến của bác sĩ da liễu.
""")

        # Template cho thông tin về mức độ nguy hại
        self.env.from_string("""
{%- set dangerous_ingredients = [] %}
{%- for ing in ingredients_data %}
{%-   if ing.hazard_level|lower in ["cao", "high", "trung bình", "medium"] %}
{%-     set _ = dangerous_ingredients.append(ing) %}
{%-   endif %}
{%- endfor %}

{%- if dangerous_ingredients %}
Trong số các thành phần bạn hỏi, có {{ dangerous_ingredients|length }} thành phần có mức độ nguy hại đáng chú ý:

{% for ingredient in dangerous_ingredients %}
{{ loop.index }}. {{ ingredient.hazard_level|get_hazard_emoji }} {{ ingredient.name }} (Mức độ nguy hại: {{ ingredient.hazard_level }})
   {{ ingredient.description }}
{%- if ingredient.effects and ingredient.effects|length > 0 %}
   Tác động tiềm ẩn: {{ ingredient.effects|join(', ') }}
{%- endif %}

{% endfor %}
{%- else %}
Tốt quá! Các thành phần bạn hỏi đều có mức độ nguy hại thấp hoặc không có thông tin về tác động tiêu cực đáng kể.
{%- endif %}

Lưu ý: Thông tin trên chỉ mang tính tham khảo. Mỗi người có thể phản ứng khác nhau với các thành phần mỹ phẩm. Nếu bạn có làn da nhạy cảm, hãy tham khảo ý kiến của bác sĩ da liễu.
""")

        # Template cho thông tin về an toàn
        self.env.from_string("""
{%- set safe_ingredients = [] %}
{%- for ing in ingredients_data %}
{%-   if ing.hazard_level|lower in ["an toàn", "low", "thấp"] %}
{%-     set _ = safe_ingredients.append(ing) %}
{%-   endif %}
{%- endfor %}

{%- if safe_ingredients %}
Trong số các thành phần bạn hỏi, có {{ safe_ingredients|length }} thành phần được đánh giá là an toàn:

{% for ingredient in safe_ingredients %}
{{ loop.index }}. 🟢 {{ ingredient.name }} (Mức độ nguy hại: {{ ingredient.hazard_level }})
   {{ ingredient.description }}

{% endfor %}
{%- else %}
Tôi không tìm thấy thành phần nào có mức độ an toàn cao trong danh sách bạn hỏi. Hãy cân nhắc tìm các sản phẩm thay thế.
{%- endif %}

Lưu ý: Thông tin trên chỉ mang tính tham khảo. Mỗi người có thể phản ứng khác nhau với các thành phần mỹ phẩm. Nếu bạn có làn da nhạy cảm, hãy tham khảo ý kiến của bác sĩ da liễu.
""")

        # Template cho thông tin về thành phần thay thế
        self.env.from_string("""
Dưới đây là một số thành phần thay thế an toàn hơn:

{% for ingredient in ingredients_data %}
{{ loop.index }}. 
{%- if ingredient.alternatives and ingredient.alternatives|length > 0 %}
 Thay vì {{ ingredient.name }} (Mức độ nguy hại: {{ ingredient.hazard_level }}), bạn có thể tìm các sản phẩm chứa:
   {{ ingredient.alternatives|join(', ') }}
{%- else %}
 Với {{ ingredient.name }} (Mức độ nguy hại: {{ ingredient.hazard_level }}), hiện chưa có thông tin về thành phần thay thế.
{%- endif %}

{% endfor %}

Lưu ý: Thông tin trên chỉ mang tính tham khảo. Mỗi người có thể phản ứng khác nhau với các thành phần mỹ phẩm. Nếu bạn có làn da nhạy cảm, hãy tham khảo ý kiến của bác sĩ da liễu.
""")

    def generate_response(self, intent: str, ingredients_data: List[Dict[str, Any]], original_query: str) -> str:
        """
        Tạo câu trả lời dựa trên intent và dữ liệu về thành phần

        Args:
            intent: Loại ý định của người dùng
            ingredients_data: Danh sách thông tin về các thành phần
            original_query: Câu hỏi gốc của người dùng

        Returns:
            Câu trả lời được tạo ra
        """
        if not ingredients_data:
            # Sử dụng template cho trường hợp không tìm thấy
            template = self.env.get_template("not_found")
            return template.render()

        # Xác định template dựa trên intent
        template_name = intent
        if intent not in ["ingredient_info", "hazard_info", "safety_info", "alternative_info"]:
            template_name = "ingredient_info"  # Template mặc định

        # Lấy template tương ứng
        template = self.env.get_template(template_name)

        # Render template với dữ liệu
        return template.render(
            ingredients_data=ingredients_data,
            original_query=original_query
        )
