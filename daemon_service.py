"""
Linux Service - Queue удирдлага хийх Python Daemon
Архитектур: WebUI → Linux Service → AI Module
"""

import os
import sys
import time
import json
import redis
import logging
import signal
from datetime import datetime
from typing import Dict, Optional
import requests

# Logging тохиргоо
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/invoice_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InvoiceDaemon:
    """
    Баримтын хүсэлтийг queue-д оруулж, эргэх хариу өгөх daemon
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.queue_name = "invoice_queue"
        self.running = False
        self.pid_file = '/var/run/invoice_daemon.pid'
        
    def start(self):
        """
        Daemon эхлүүлэх
        """
        # PID file үүсгэх
        self._create_pid_file()
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.running = True
        logger.info("Invoice Daemon эхэллээ...")
        
        while self.running:
            try:
                # Health check
                self._health_check()
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Daemon алдаа: {e}")
                time.sleep(1)
    
    def stop(self):
        """
        Daemon зогсоох
        """
        logger.info("Daemon зогсож байна...")
        self.running = False
        self._remove_pid_file()
    
    def add_to_queue(self, invoice_data: Dict) -> str:
        """
        Баримтыг queue-д нэмэх
        
        Args:
            invoice_data: Баримтын өгөгдөл
            
        Returns:
            Job ID
        """
        try:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            queue_item = {
                "id": job_id,
                "data": invoice_data,
                "created_at": datetime.now().isoformat(),
                "status": "queued"
            }
            
            # Queue-д хийх
            self.redis_client.lpush(
                self.queue_name,
                json.dumps(queue_item, ensure_ascii=False)
            )
            
            logger.info(f"Queue-д нэмэгдлээ: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Queue нэмэх алдаа: {e}")
            raise
    
    def get_result(self, job_id: str, timeout: int = 30) -> Optional[Dict]:
        """
        Ажлын үр дүн авах
        
        Args:
            job_id: Ажлын ID
            timeout: Хүлээх хугацаа (секунд)
            
        Returns:
            Үр дүн эсвэл None
        """
        result_key = f"result:{job_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = self.redis_client.get(result_key)
                if result:
                    return json.loads(result)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Үр дүн авах алдаа: {e}")
                return None
        
        logger.warning(f"Timeout: {job_id}")
        return None
    
    def _health_check(self):
        """
        Систем эрүүл эсэхийг шалгах
        """
        try:
            # Redis холболт шалгах
            self.redis_client.ping()
            
            # Queue хэмжээ шалгах
            queue_size = self.redis_client.llen(self.queue_name)
            if queue_size > 1000:
                logger.warning(f"Queue хэт их: {queue_size}")
                
        except Exception as e:
            logger.error(f"Health check алдаа: {e}")
    
    def _create_pid_file(self):
        """
        PID file үүсгэх
        """
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"PID file үүсгэх алдаа: {e}")
    
    def _remove_pid_file(self):
        """
        PID file устгах
        """
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except Exception as e:
            logger.error(f"PID file устгах алдаа: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        Signal handler
        """
        logger.info(f"Signal хүлээн авсан: {signum}")
        self.stop()
        sys.exit(0)


class DaemonController:
    """
    Daemon удирдлага хийх controller
    """
    
    @staticmethod
    def start():
        """Daemon эхлүүлэх"""
        daemon = InvoiceDaemon()
        daemon.start()
    
    @staticmethod
    def stop():
        """Daemon зогсоох"""
        pid_file = '/var/run/invoice_daemon.pid'
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Daemon зогслоо: PID {pid}")
        except FileNotFoundError:
            logger.error("Daemon ажиллаагүй байна")
        except Exception as e:
            logger.error(f"Daemon зогсоох алдаа: {e}")
    
    @staticmethod
    def restart():
        """Daemon дахин эхлүүлэх"""
        DaemonController.stop()
        time.sleep(2)
        DaemonController.start()
    
    @staticmethod
    def status():
        """Daemon статус шалгах"""
        pid_file = '/var/run/invoice_daemon.pid'
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Process ажиллаж байгаа эсэхийг шалгах
            os.kill(pid, 0)
            logger.info(f"Daemon ажиллаж байна: PID {pid}")
            return True
        except (FileNotFoundError, ProcessLookupError):
            logger.info("Daemon ажиллаагүй байна")
            return False
        except Exception as e:
            logger.error(f"Статус шалгах алдаа: {e}")
            return False


def main():
    """
    Daemon удирдах CLI
    """
    if len(sys.argv) < 2:
        print("Хэрэглээ: python daemon_service.py {start|stop|restart|status}")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'start':
        DaemonController.start()
    elif command == 'stop':
        DaemonController.stop()
    elif command == 'restart':
        DaemonController.restart()
    elif command == 'status':
        DaemonController.status()
    else:
        print(f"Тодорхойгүй команд: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
