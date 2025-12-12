# celery.py
# Энэ файлыг project-ийн үндсэн folder-т байрлуулна (settings.py-тай хамт)
# Жишээ: myproject/myproject/celery.py

import os
from celery import Celery
from celery.schedules import crontab

# Django settings module тохируулах
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barimt_zasvarlagch.settings')  # 'myproject' -> өөрийн project нэрээр солино

app = Celery('barimt_zasvarlagch')  # 'myproject' -> өөрийн project нэрээр солино

# Django settings-ээс CELERY_ prefix-тэй тохиргоонуудыг уншина
app.config_from_object('django.conf:settings', namespace='CELERY')

# Бүх app-уудаас tasks.py файлуудыг автоматаар олно
app.autodiscover_tasks()


# Celery Beat Schedule - Шөнийн 1 цагт ажиллах
app.conf.beat_schedule = {
    'process-downloads-at-1am': {
        'task': 'yourapp.tasks.process_pending_downloads',  # 'yourapp' -> өөрийн app нэрээр солино
        'schedule': crontab(hour=1, minute=0),  # Шөнийн 1:00 цагт
        # 'schedule': crontab(minute='*/5'),  # Тест: 5 минут тутамд
    },
}

app.conf.timezone = 'Asia/Ulaanbaatar'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')