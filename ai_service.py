"""
AI Module - Баримтын мэдээллийг боловсруулах AI сервис
Архитектур: WebUI → Linux Service → AI Module → Database
"""

import os
import json
import time
import redis
import logging
from openai import OpenAI
from datetime import datetime
from typing import Dict, Optional, List

# Logging тохиргоо
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIInvoiceProcessor:
    """
    OpenAI ашиглан баримтын мэдээллийг боловсруулах AI модуль
    """
    
    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
    def extract_invoice_info(self, raw_data: Dict) -> Dict:
        """
        Баримтын өгөгдлөөс мэдээлэл ялгаж авах
        
        Args:
            raw_data: Боловсруулах өгөгдөл
            
        Returns:
            Боловсруулсан мэдээлэл
        """
        try:
            prompt = self._build_extraction_prompt(raw_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Та баримтын мэдээлэл боловсруулдаг AI туслах. "
                                   "Өгөгдлийг шалгаж, алдаа илрүүлж, зөв форматад оруулна."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Амжилттай боловсруулав: {result.get('billId', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI боловсруулалтын алдаа: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _build_extraction_prompt(self, data: Dict) -> str:
        """
        Prompt үүсгэх
        """
        return f"""
Дараах баримтын мэдээллийг шинжлэн JSON форматаар буцаа:

Өгөгдөл:
{json.dumps(data, ensure_ascii=False, indent=2)}

Хийх ажил:
1. totalAmount зөв эсэхийг шалга (сөрөг тоо, 0, хэт их дүн байж болохгүй)
2. companyReg регистрийн форматыг шалга (7 оронтой тоо байх ёстой)
3. storeNo дэлгүүрийн дугаар зөв эсэхийг шалга
4. Огноо timestamp зөв эсэхийг баталга

Буцаах формат:
{{
    "is_valid": true/false,
    "errors": ["алдааны жагсаалт"],
    "validated_data": {{
        "totalAmount": "зассан дүн",
        "companyReg": "зассан регистр",
        "storeNo": "дэлгүүрийн дугаар",
        "billType": "1 эсвэл 3"
    }},
    "suggestions": ["санал"]
}}
"""

    def validate_and_fix(self, invoice_data: Dict) -> Dict:
        """
        Баримтын өгөгдлийг шалгаж, засварлах
        """
        try:
            # Үндсэн шалгалтууд
            errors = []
            fixed_data = invoice_data.copy()
            
            # Дүнгийн шалгалт
            total_amount = float(invoice_data.get('totalAmount', 0))
            if total_amount <= 0:
                errors.append(f"Буруу дүн: {total_amount}")
            elif total_amount > 100000000:  # 100 сая
                errors.append(f"Хэт их дүн: {total_amount}")
                
            # Регистрийн шалгалт
            company_reg = str(invoice_data.get('companyReg', ''))
            if company_reg and len(company_reg) != 7:
                errors.append(f"Регистрийн дугаар буруу: {company_reg}")
                
            # AI-ээр нарийвчлан шалгуулах
            if errors:
                ai_result = self.extract_invoice_info(invoice_data)
                fixed_data = ai_result.get('validated_data', fixed_data)
                
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "fixed_data": fixed_data
            }
            
        except Exception as e:
            logger.error(f"Баталгаажуулалтын алдаа: {e}")
            return {
                "is_valid": False,
                "errors": [str(e)],
                "fixed_data": invoice_data
            }
    
    def process_queue_item(self, queue_item: Dict) -> Dict:
        """
        Queue-с ирсэн ажлыг боловсруулах
        """
        try:
            logger.info(f"Queue ажил эхэллээ: {queue_item.get('id')}")
            
            # 1. Баталгаажуулалт
            validation = self.validate_and_fix(queue_item)
            
            if not validation['is_valid']:
                logger.warning(f"Баталгаажуулалт амжилтгүй: {validation['errors']}")
                return {
                    "status": "validation_failed",
                    "errors": validation['errors'],
                    "original_data": queue_item
                }
            
            # 2. AI боловсруулалт
            processed = self.extract_invoice_info(validation['fixed_data'])
            
            # 3. Үр дүн
            return {
                "status": "success",
                "processed_data": processed,
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"Queue боловсруулалтын алдаа: {e}")
            return {
                "status": "error",
                "error": str(e),
                "original_data": queue_item
            }


class QueueWorker:
    """
    Redis Queue-тэй ажиллах daemon процесс
    """
    
    def __init__(self, processor: AIInvoiceProcessor):
        self.processor = processor
        self.redis_client = processor.redis_client
        self.queue_name = "invoice_queue"
        self.running = False
        
    def start(self):
        """
        Worker эхлүүлэх
        """
        self.running = True
        logger.info("AI Queue Worker эхэллээ...")
        
        while self.running:
            try:
                # Queue-с ажил авах (blocking with timeout)
                item = self.redis_client.brpop(self.queue_name, timeout=5)
                
                if item:
                    _, queue_data = item
                    queue_item = json.loads(queue_data)
                    
                    # Боловсруулалт
                    result = self.processor.process_queue_item(queue_item)
                    
                    # Үр дүнг result queue-д хийх
                    self._store_result(queue_item.get('id'), result)
                    
            except KeyboardInterrupt:
                logger.info("Worker зогссон...")
                self.running = False
            except Exception as e:
                logger.error(f"Worker алдаа: {e}")
                time.sleep(1)
    
    def _store_result(self, job_id: str, result: Dict):
        """
        Үр дүнг Redis-д хадгалах
        """
        try:
            result_key = f"result:{job_id}"
            self.redis_client.setex(
                result_key,
                3600,  # 1 цаг хадгална
                json.dumps(result, ensure_ascii=False)
            )
            logger.info(f"Үр дүн хадгалагдлаа: {job_id}")
        except Exception as e:
            logger.error(f"Үр дүн хадгалах алдаа: {e}")


def main():
    """
    AI Service эхлүүлэх
    """
    # OpenAI API key шалгах
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY тохируулаагүй байна!")
        return
    
    # AI Processor үүсгэх
    processor = AIInvoiceProcessor(api_key=api_key)
    
    # Queue Worker эхлүүлэх
    worker = QueueWorker(processor)
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Сервис зогслоо.")


if __name__ == "__main__":
    main()
