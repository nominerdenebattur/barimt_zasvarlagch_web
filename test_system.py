#!/usr/bin/env python3
"""
Системийн тест скрипт
AI Invoice Processing System-ийн бүх компонентыг шалгана
"""

import sys
import time
import json
import redis
import requests
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

class SystemTester:
    def __init__(self):
        self.redis_client = None
        self.test_results = []
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}{text}")
        print(f"{Fore.CYAN}{'='*50}\n")
    
    def print_success(self, text):
        print(f"{Fore.GREEN}✓ {text}")
        self.test_results.append(("success", text))
    
    def print_error(self, text):
        print(f"{Fore.RED}✗ {text}")
        self.test_results.append(("error", text))
    
    def print_warning(self, text):
        print(f"{Fore.YELLOW}⚠ {text}")
        self.test_results.append(("warning", text))
    
    def test_redis_connection(self):
        """Redis холболт шалгах"""
        self.print_header("1. Redis холболт шалгаж байна...")
        
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            self.print_success("Redis холболт амжилттай")
            return True
        except Exception as e:
            self.print_error(f"Redis холболт амжилтгүй: {e}")
            return False
    
    def test_queue_operations(self):
        """Queue үйлдлүүд шалгах"""
        self.print_header("2. Queue үйлдлүүд шалгаж байна...")
        
        try:
            # Test queue нэмэх
            test_data = {
                "id": "test_job_001",
                "data": {
                    "totalAmount": "10000",
                    "companyReg": "1234567",
                    "storeNo": "160"
                },
                "created_at": datetime.now().isoformat()
            }
            
            self.redis_client.lpush(
                "test_queue",
                json.dumps(test_data, ensure_ascii=False)
            )
            self.print_success("Queue-д өгөгдөл нэмэх амжилттай")
            
            # Queue-с авах
            result = self.redis_client.rpop("test_queue")
            if result:
                data = json.loads(result)
                self.print_success(f"Queue-с өгөгдөл авах амжилттай: {data['id']}")
            else:
                self.print_error("Queue-с өгөгдөл авч чадсангүй")
                return False
            
            return True
            
        except Exception as e:
            self.print_error(f"Queue үйлдэл амжилтгүй: {e}")
            return False
    
    def test_openai_connection(self):
        """OpenAI API холболт шалгах"""
        self.print_header("3. OpenAI API шалгаж байна...")
        
        try:
            import os
            from openai import OpenAI
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                self.print_warning("OPENAI_API_KEY тохируулаагүй байна (.env файлд нэмнэ үү)")
                return False
            
            client = OpenAI(api_key=api_key)
            
            # Simple test completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Say 'test successful' if you can read this."}
                ],
                max_tokens=10
            )
            
            self.print_success("OpenAI API холболт амжилттай")
            return True
            
        except ImportError:
            self.print_warning("openai package суугаагүй байна (pip install openai)")
            return False
        except Exception as e:
            self.print_error(f"OpenAI API холболт амжилтгүй: {e}")
            return False
    
    def test_daemon_process(self):
        """Daemon процесс ажиллаж байгаа эсэхийг шалгах"""
        self.print_header("4. Daemon процесс шалгаж байна...")
        
        try:
            import os
            
            pid_file = '/var/run/invoice_daemon.pid'
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Process ажиллаж байгаа эсэхийг шалгах
                try:
                    os.kill(pid, 0)
                    self.print_success(f"Daemon процесс ажиллаж байна (PID: {pid})")
                    return True
                except OSError:
                    self.print_warning(f"Daemon PID файл байгаа ч процесс ажиллахгүй байна")
                    return False
            else:
                self.print_warning("Daemon эхлээгүй байна (systemctl start invoice-daemon)")
                return False
                
        except Exception as e:
            self.print_error(f"Daemon шалгалт амжилтгүй: {e}")
            return False
    
    def test_end_to_end(self):
        """End-to-end тест"""
        self.print_header("5. End-to-End тест хийж байна...")
        
        try:
            # Test invoice data
            invoice_data = {
                "totalAmount": "15000",
                "companyReg": "7654321",
                "storeNo": "160",
                "billType": "1"
            }
            
            job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            queue_item = {
                "id": job_id,
                "data": invoice_data,
                "created_at": datetime.now().isoformat(),
                "status": "queued"
            }
            
            # Queue-д хийх
            self.redis_client.lpush(
                "invoice_queue",
                json.dumps(queue_item, ensure_ascii=False)
            )
            self.print_success(f"Тест job үүсгэв: {job_id}")
            
            # Үр дүн хүлээх (30 секунд)
            result_key = f"result:{job_id}"
            timeout = 30
            start_time = time.time()
            
            print(f"{Fore.YELLOW}Үр дүн хүлээж байна (timeout: {timeout}s)...")
            
            while time.time() - start_time < timeout:
                result = self.redis_client.get(result_key)
                if result:
                    result_data = json.loads(result)
                    self.print_success(f"Үр дүн хүлээн авлаа: {result_data.get('status')}")
                    
                    if result_data.get('status') == 'success':
                        self.print_success("End-to-End тест амжилттай!")
                        return True
                    else:
                        self.print_warning(f"Validation амжилтгүй: {result_data.get('errors')}")
                        return True  # Тест ажиллав гэсэн үг
                
                time.sleep(1)
            
            self.print_warning(f"Timeout - Daemon/AI service ажиллахгүй байж магадгүй")
            return False
            
        except Exception as e:
            self.print_error(f"End-to-End тест амжилтгүй: {e}")
            return False
    
    def test_django_connection(self):
        """Django app ажиллаж байгаа эсэхийг шалгах"""
        self.print_header("6. Django app шалгаж байна...")
        
        try:
            # Локал Django сервер шалгах
            response = requests.get('http://localhost:8000/', timeout=5)
            
            if response.status_code == 200:
                self.print_success("Django app ажиллаж байна")
                return True
            else:
                self.print_warning(f"Django app хариу өгсөн боловч статус: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_warning("Django app ажиллахгүй байна (python manage.py runserver)")
            return False
        except Exception as e:
            self.print_error(f"Django шалгалт амжилтгүй: {e}")
            return False
    
    def print_summary(self):
        """Тестийн дүнг хэвлэх"""
        self.print_header("Тестийн дүн")
        
        success_count = sum(1 for status, _ in self.test_results if status == "success")
        error_count = sum(1 for status, _ in self.test_results if status == "error")
        warning_count = sum(1 for status, _ in self.test_results if status == "warning")
        
        total = len(self.test_results)
        
        print(f"{Fore.GREEN}Амжилттай: {success_count}/{total}")
        print(f"{Fore.RED}Алдаа: {error_count}/{total}")
        print(f"{Fore.YELLOW}Анхааруулга: {warning_count}/{total}")
        
        if error_count == 0 and warning_count == 0:
            print(f"\n{Fore.GREEN}{'='*50}")
            print(f"{Fore.GREEN}🎉 Бүх тест амжилттай боллоо!")
            print(f"{Fore.GREEN}{'='*50}\n")
        elif error_count == 0:
            print(f"\n{Fore.YELLOW}{'='*50}")
            print(f"{Fore.YELLOW}⚠️  Тест дууслаа (анхааруулгатай)")
            print(f"{Fore.YELLOW}{'='*50}\n")
        else:
            print(f"\n{Fore.RED}{'='*50}")
            print(f"{Fore.RED}❌ Зарим тест амжилтгүй боллоо")
            print(f"{Fore.RED}{'='*50}\n")
    
    def run_all_tests(self):
        """Бүх тестийг ажиллуулах"""
        print(f"{Fore.MAGENTA}{'='*50}")
        print(f"{Fore.MAGENTA}AI Invoice Processing System - Тест эхэллээ")
        print(f"{Fore.MAGENTA}{'='*50}\n")
        
        tests = [
            self.test_redis_connection,
            self.test_queue_operations,
            self.test_openai_connection,
            self.test_daemon_process,
            self.test_django_connection,
            self.test_end_to_end,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.print_error(f"Тест алдаа: {e}")
            
            time.sleep(0.5)
        
        self.print_summary()


def main():
    tester = SystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    # Colorama суулгах шаардлагатай
    try:
        import colorama
    except ImportError:
        print("colorama package хэрэгтэй: pip install colorama")
        sys.exit(1)
    
    main()
