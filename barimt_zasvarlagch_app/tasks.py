# tasks.py - Celery tasks
# Энэ файлыг your_app/ folder дотор үүсгэнэ (views.py-тай хамт)

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone

# API тохиргоо
TOKEN_URL = "https://auth.itc.gov.mn/auth/realms/ITC/protocol/openid-connect/token"
SERVICE_URL = "https://api.ebarimt.mn/api/tpi/receipt/getSalesTotalData"
API_KEY = "ae7368b03a55e135398668d964b5176e3e7f9c4f"

TOKEN_PAYLOAD = {
    "client_id": "invoice",
    "grant_type": "password",
    "username": "ЖЮ00220821",
    "password": "Saiko@0208"
}


def get_access_token():
    # Token авах
    try:
        response = requests.post(TOKEN_URL, data=TOKEN_PAYLOAD, timeout=30)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Token авахад алдаа: {e}")
        return None


def fetch_data_for_date(date_obj, status):
    # Тухайн өдрийн өгөгдөл татах
    access_token = get_access_token()
    if not access_token:
        return None, "Token авч чадсангүй"

    headers = {
        "x-api-key": API_KEY,
        "Authorization": f"Bearer {access_token}"
    }

    request_payload = {
        "year": str(date_obj.year),
        "month": str(date_obj.month),
        "day": str(date_obj.day),
        "status": status,
        "startCount": 1,
        "endCount": 250000
    }

    try:
        response = requests.post(
            SERVICE_URL,
            headers=headers,
            json=request_payload,
            timeout=120
        )
        response.raise_for_status()

        if response.text:
            json_response = response.json()
            data_list = json_response.get('data', {}).get('list', [])
            return data_list, None
        return [], None

    except Exception as e:
        return None, str(e)


def get_month_folder(date_obj):
    # Сарын folder нэр үүсгэх: C:\YYYY_MM-р сар_задаргаа\
    month_names = ['1-р сар', '2-р сар', '3-р сар', '4-р сар', '5-р сар', '6-р сар',
                   '7-р сар', '8-р сар', '9-р сар', '10-р сар', '11-р сар', '12-р сар']
    folder_name = f"{date_obj.year}_{month_names[date_obj.month - 1]}_задаргаа"
    return os.path.join("C:\\", folder_name)


def ensure_folder_exists(folder_path):
    # Folder байхгүй бол үүсгэх
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


@shared_task
def process_single_download(schedule_id):
    # Нэг таталтын хүсэлтийг боловсруулах

    # Import here to avoid circular imports
    from .models import DownloadSchedule

    try:
        schedule = DownloadSchedule.objects.get(id=schedule_id)

        # Хэрэв цуцлагдсан бол алгасах
        if schedule.download_status == 'cancelled':
            return f"Schedule {schedule_id} цуцлагдсан"

        # Төлөв шинэчлэх
        schedule.download_status = 'processing'
        schedule.started_at = timezone.now()
        schedule.save()

        # Өгөгдөл татах
        all_data = []
        current_date = schedule.start_date

        while current_date <= schedule.end_date:
            # Цуцлагдсан эсэхийг шалгах
            schedule.refresh_from_db()
            if schedule.download_status == 'cancelled':
                return f"Schedule {schedule_id} цуцлагдсан"

            data, error = fetch_data_for_date(current_date, schedule.status)
            if data:
                for item in data:
                    item['fetch_date'] = str(current_date)
                all_data.extend(data)

            current_date += timedelta(days=1)

        if not all_data:
            schedule.download_status = 'completed'
            schedule.completed_at = timezone.now()
            schedule.total_records = 0
            schedule.save()
            return f"Schedule {schedule_id}: Өгөгдөл олдсонгүй"

        # Excel файл үүсгэх
        df = pd.DataFrame(all_data)

        # Folder үүсгэх
        output_folder = get_month_folder(schedule.start_date)
        ensure_folder_exists(output_folder)

        # Файлын нэр
        status_name = schedule.get_status_name()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"barimt_{status_name}_{schedule.start_date}_{schedule.end_date}_{timestamp}.xlsx"
        full_path = os.path.join(output_folder, filename)

        # Хадгалах
        df.to_excel(full_path, index=False)

        # Төлөв шинэчлэх
        schedule.download_status = 'completed'
        schedule.completed_at = timezone.now()
        schedule.file_path = full_path
        schedule.total_records = len(all_data)
        schedule.save()

        return f"Schedule {schedule_id}: {len(all_data)} бичлэг -> {full_path}"

    except Exception as e:
        # Алдаа бичих
        try:
            from .models import DownloadSchedule
            schedule = DownloadSchedule.objects.get(id=schedule_id)
            schedule.download_status = 'failed'
            schedule.error_message = str(e)
            schedule.completed_at = timezone.now()
            schedule.save()
        except:
            pass
        return f"Schedule {schedule_id} алдаа: {str(e)}"


@shared_task
def process_pending_downloads():
    # Шөнийн 1 цагт ажиллах task
    # Бүх pending төлөвтэй хүсэлтүүдийг боловсруулна
    from .models import DownloadSchedule

    pending_schedules = DownloadSchedule.objects.filter(download_status='pending')

    results = []
    for schedule in pending_schedules:
        result = process_single_download(schedule.id)
        results.append(result)

    return results