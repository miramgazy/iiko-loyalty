import io
import os
import re
import json
import base64
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from PIL import Image, ImageOps
from pypdf import PdfReader

from apps.core.models import Organization

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Вы — экспертный ассистент по распознаванию и оцифровке приходных товарных накладных (ТОРГ-12, УПД, товарный чек, накладная поставщика) для ресторанного учета.
Вам предоставлены страницы одного документа (фото или скан).

Задача:
Внимательно извлеките метаданные накладной и ВСЕ строки товарных позиций в виде строгого JSON-документа.
Если документ рукописный или имеет сложный почерк/смазанные участки, сделайте максимально точную транскрипцию.

Правила:
1. "invoice_number": Номер накладной (строка, без лишних символов "№"). Если номера нет, оставьте пустую строку "".
2. "invoice_date": Дата накладной в формате YYYY-MM-DD. Если год не указан явно, ориентируйтесь на текущий или контекст. Если дата не найдена, укажите null.
3. "supplier_name": Полное или краткое наименование поставщика/грузоотправителя (строка).
4. "supplier_inn": ИНН или БИН поставщика (строка цифр, если есть в реквизитах или штампе, иначе "").
5. "total_sum": Итоговая сумма по всей накладной («Всего к оплате» / «Итого с НДС»), число с плавающей точкой (float).
6. "vat_sum": Общая сумма НДС документа (если указана, иначе 0.0).
7. "items": Массив объектов позиций товаров. Каждая строка содержит:
   - "num": Номер по порядку (целое число 1, 2, 3...)
   - "raw_name": Точное наименование товара из накладной (как написано в документе, включая сорт, жирность, калибр)
   - "clean_name": Очищенное смысловое наименование товара для ресторанного учета в iiko (удалите бренд, производителя, ТОО/ИП, артикулы, упаковку/тару и лишние слова. Например: из 'Сыр Моцарелла для пиццы 45% блок 2кг Бонфесто Беларусь' -> 'Сыр Моцарелла 45%', из 'Томаты тепличные сорт Сливка 1 кат. ящик 5кг ТОО Агро' -> 'Томаты Сливка', из 'Молоко питьевое паст. 3.2% тетрапак 1л Домик в деревне' -> 'Молоко 3.2%')
   - "raw_unit": Единица измерения (например: "кг", "шт", "л", "бут", "уп", "кор", "бан")
   - "raw_amount": Количество (число float, без единиц измерения, дробная часть через точку)
   - "raw_price": Цена за единицу измерения (число float)
   - "raw_sum": Итоговая сумма по этой строке (число float)
   - "raw_vat_percent": Процент НДС для строки (например 0, 10, 20 или null)
   - "packaging_hint": Любая подсказка о фасовке из текста (например: "10 кг в кор.", "бут 0.75л", "пачка 180г", если явных данных нет — "")

В ответе должен быть ТОЛЬКО валидный JSON-объект без markdown-разметки и пояснений:
{
  "invoice_number": "...",
  "invoice_date": "YYYY-MM-DD",
  "supplier_name": "...",
  "supplier_inn": "...",
  "total_sum": 0.0,
  "vat_sum": 0.0,
  "items": [
    {
      "num": 1,
      "raw_name": "...",
      "clean_name": "...",
      "raw_unit": "...",
      "raw_amount": 0.0,
      "raw_price": 0.0,
      "raw_sum": 0.0,
      "raw_vat_percent": 0.0,
      "packaging_hint": "..."
    }
  ]
}
"""


def optimize_image_for_vision(image_bytes: bytes, max_size: int = 1920) -> bytes:
    """
    Автоматически корректирует EXIF ориентацию и уменьшает изображение
    для снижения задержки и экономии токенов.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            w, h = img.size
            if max(w, h) > max_size:
                ratio = max_size / max(w, h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=85, optimize=True)
            return out.getvalue()
    except Exception as e:
        logger.warning(f"Error optimizing image: {e}")
        return image_bytes


def extract_images_from_pdf(pdf_bytes: bytes) -> List[bytes]:
    """
    Извлекает внедренные изображения из PDF или возвращает исходный PDF байты.
    """
    images = []
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            for image_file in page.images:
                images.append(optimize_image_for_vision(image_file.data))
    except Exception as e:
        logger.warning(f"Could not extract images from PDF via pypdf: {e}")
    return images


def parse_json_from_llm_response(text: str) -> dict:
    """
    Безопасный парсер JSON ответа от LLM.
    """
    text = text.strip()
    
    # 1. Попытка распарсить как есть
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Поиск блока ```json ... ```
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Поиск первого '{' и последнего '}'
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except Exception:
            pass

    raise ValueError(f"Не удалось извлечь структурированный JSON из ответа модели: {text[:200]}...")


class BaseVisionAdapter(ABC):
    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

    @abstractmethod
    def extract_invoice_data(self, image_items: List[Dict[str, Any]]) -> dict:
        """
        image_items: список словарей [{'bytes': b'...', 'mime_type': 'image/jpeg' или 'application/pdf'}]
        """
        pass


class GeminiVisionAdapter(BaseVisionAdapter):
    def extract_invoice_data(self, image_items: List[Dict[str, Any]]) -> dict:
        model = self.model_name or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        if self.base_url:
            url = f"{self.base_url.rstrip('/')}/v1beta/models/{model}:generateContent?key={self.api_key}"

        parts = [{"text": SYSTEM_PROMPT}]

        for item in image_items:
            data_b64 = base64.b64encode(item['bytes']).decode('utf-8')
            mime = item.get('mime_type', 'image/jpeg')
            parts.append({
                "inlineData": {
                    "mimeType": mime,
                    "data": data_b64
                }
            })

        payload = {
            "contents": [{
                "role": "user",
                "parts": parts
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            res_data = response.json()

        try:
            candidate = res_data["candidates"][0]
            content_part = candidate["content"]["parts"][0]["text"]
            return parse_json_from_llm_response(content_part)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Некорректный формат ответа Gemini: {res_data}") from e


class OpenAIVisionAdapter(BaseVisionAdapter):
    def extract_invoice_data(self, image_items: List[Dict[str, Any]]) -> dict:
        model = self.model_name or "gpt-4o"
        url = (self.base_url or "https://api.openai.com/v1").rstrip('/') + "/chat/completions"

        content_items = [{"type": "text", "text": SYSTEM_PROMPT}]

        for item in image_items:
            mime = item.get('mime_type', 'image/jpeg')
            data_b64 = base64.b64encode(item['bytes']).decode('utf-8')
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{data_b64}",
                    "detail": "high"
                }
            })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": content_items}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            res_data = response.json()

        try:
            content = res_data["choices"][0]["message"]["content"]
            return parse_json_from_llm_response(content)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Некорректный формат ответа OpenAI: {res_data}") from e


class AnthropicVisionAdapter(BaseVisionAdapter):
    def extract_invoice_data(self, image_items: List[Dict[str, Any]]) -> dict:
        model = self.model_name or "claude-3-5-sonnet-20241022"
        url = (self.base_url or "https://api.anthropic.com/v1").rstrip('/') + "/messages"

        content_items = []
        for item in image_items:
            mime = item.get('mime_type', 'image/jpeg')
            data_b64 = base64.b64encode(item['bytes']).decode('utf-8')
            content_items.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": data_b64
                }
            })

        content_items.append({
            "type": "text",
            "text": "Распознайте данную накладную строго по системным правилам в JSON."
        })

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": content_items}
            ],
            "max_tokens": 4096,
            "temperature": 0.1
        }

        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            res_data = response.json()

        try:
            content = res_data["content"][0]["text"]
            return parse_json_from_llm_response(content)
        except (KeyError, IndexError) as e:
            raise ValueError(f"Некорректный формат ответа Anthropic: {res_data}") from e


class VisionInvoiceService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.provider = organization.vision_llm_provider or 'gemini'
        self.model = organization.vision_llm_model or 'gemini-2.5-flash'
        self.api_key = organization.vision_llm_api_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        self.base_url = organization.vision_llm_base_url

        if not self.api_key:
            raise ValueError("API-ключ для Vision LLM не настроен в организации и отсутствует в системных переменных")

    def _get_adapter(self) -> BaseVisionAdapter:
        if self.provider == 'gemini':
            return GeminiVisionAdapter(self.api_key, self.model, self.base_url)
        elif self.provider in ('openai', 'deepseek'):
            return OpenAIVisionAdapter(self.api_key, self.model, self.base_url)
        elif self.provider == 'anthropic':
            return AnthropicVisionAdapter(self.api_key, self.model, self.base_url)
        else:
            return GeminiVisionAdapter(self.api_key, self.model, self.base_url)

    def process_invoice(self, invoice) -> dict:
        """
        Считывает изображения/PDF накладной, подготавливает и отправляет в выбранный Vision LLM.
        """
        image_items = []
        images = invoice.images.all().order_by('page_number', 'id')

        if not images.exists():
            raise ValueError("У накладной отсутствуют загруженные изображения или страницы")

        for img_obj in images:
            file_bytes = img_obj.image.read()
            filename = img_obj.image.name.lower()

            if img_obj.is_pdf or filename.endswith('.pdf'):
                # Если провайдер Gemini - он нативно принимает application/pdf
                if self.provider == 'gemini':
                    image_items.append({
                        'bytes': file_bytes,
                        'mime_type': 'application/pdf'
                    })
                else:
                    # Извлекаем внедренные изображения страниц
                    extracted = extract_images_from_pdf(file_bytes)
                    if extracted:
                        for b in extracted:
                            image_items.append({'bytes': b, 'mime_type': 'image/jpeg'})
                    else:
                        raise ValueError("Не удалось извлечь страницы из PDF для текущего Vision провайдера")
            else:
                optimized = optimize_image_for_vision(file_bytes)
                image_items.append({
                    'bytes': optimized,
                    'mime_type': 'image/jpeg'
                })

        adapter = self._get_adapter()
        extracted_data = adapter.extract_invoice_data(image_items)
        return extracted_data
