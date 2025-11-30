import os
import pandas as pd
import requests
import json

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils.datetime_safe import datetime
from openai import OpenAI

from .models import Barimt, Ebarimt_zadargaa_0, Ebarimt_zadargaa_4
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core import serializers
from requests.exceptions import HTTPError
from django.core.management.base import BaseCommand

import certifi
import redis

# Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Group-аар redirect
            if user.groups.filter(name="Hyanah").exists():
                return redirect("dashboard")
            elif user.groups.filter(name="Zasvarlah").exists():
                return redirect("zasvarlah")
            elif user.groups.filter(name="Tailan").exists():
                return redirect("compare")
            elif user.groups.filter(name="Delete").exists():
                return redirect("delete")
            # else:
            #     return render(request, 'logIn.html', {'error': 'Тухайн хэрэглэгч ямар нэг group-д хамаарахгүй байна'})
        else:
            return render(
                request, "logIn.html", {"error": "Нэвтрэх мэдээлэл буруу байна"}
            )
    return render(request, "logIn.html")

def logout_view(request):
    logout(request)
    return redirect("/")

def group_required(group_name):
    def in_group(u):
        return u.is_authenticated and u.groups.filter(name=group_name).exists()
    return user_passes_test(in_group, login_url=reverse_lazy("login"))

# def register_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         password2 = request.POST.get('password2')
#
#         if password != password2:
#             messages.error(request, "Нууц үг таарахгүй байна.")
#             return render(request, 'register.html')
#
#         if User.objects.filter(username=username).exists():
#             messages.error(request, "Ийм хэрэглэгчийн нэр аль хэдийн бүртгэлтэй байна.")
#             return render(request, 'register.html')
#
#         user = User.objects.create_user(username=username, email=email, password=password)
#         user.save()
#         messages.success(request, "Амжилттай бүртгэгдлээ! Та нэвтрэх боломжтой.")
#         return redirect('login')
#
#     return render(request, 'register.html')

def zasvarlah(request):
    selected_date = request.GET.get("selected_date", "")
    page = request.GET.get("page", 1)

    barimtuud = Barimt.objects.all().order_by("-id")
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            barimtuud = barimtuud.filter(created__gte=start_datetime, created__lt=end_datetime)
        except ValueError:
            pass

    paginator = Paginator(barimtuud, 15)  # нэг хуудсанд 15 мөр
    barimtuud_page = paginator.get_page(page)

    # barimtuud_json = serializers.serialize("json", barimtuud)

    return render(
        request,
        "zasvarlah.html",
        {
            "barimtuud": barimtuud_page,
            # "barimtuud_json": barimtuud_json,
            "page": barimtuud_page.number,
            "total_pages": paginator.num_pages,
            "has_prev": barimtuud_page.has_previous(),
            "has_next": barimtuud_page.has_next(),
            "selected_date": selected_date,
        },
    )

def ebarimt_generate(request):
    # === Input Data ===
    print("Current user:", request.user)
    print("Is authenticated:", request.user.is_authenticated)

    totalAmount = request.GET.get("totalAmount")
    regNo = request.GET.get("companyId")
    company_reg_int = str(regNo) if regNo else None

    # if regNo:
    #     billType = 1
    # else:
    #     billType = 3
    store = request.GET.get("storeId")

    vat = "1.00"
    cashAmount = totalAmount
    nonCashAmount = "0.00"
    amount = totalAmount
    cityTax = "0.00"
    billType = request.GET.get("companyFieldTypeInput")

    data = {
        "stocks": [
            {
                "measureUnit": "ширхэг",
                "code": "100541",
                "name": "Хүнсний бараа, ундаа, тамхины төрөлжсөн бус дэлгүүрийн жижиглэн худалдаа",
                "barCode": "6212",
                "qty": "1.00",
                "totalAmount": str(totalAmount),
                "cityTax": "0.00",
                "unitPrice": str(totalAmount),
                "vat": str(vat),
                "discount": "0.00",
            }
        ],
        "transID": "11120035110134",
        "cashAmount": str(cashAmount),
        "nonCashAmount": str(nonCashAmount),
        "amount": str(amount),
        "point": "0",
        "bankTransactions": [],
        "cityTax": str(cityTax),
        "vat": str(vat),
        "billType": billType,
        "customerNo": str(regNo),
        "tenderType": "",
        "amountTendered": "0.00",
        "kbTenderType": None,
        "kb_usable_lp": None,
        "tenderTypeCoupon": "",
        "amountTenderedCoupon": "0.00",
    }

    # store_str = str(store).lstrip("0") or "0"
    # store_num = int(store_str)
    # store_param = store_str

    # if store_num > 450:
    #     url = f"http://10.10.90.234/23/api/?store={store_param}put"
    # else:
    #     url = f"http://10.10.90.233/23/api/?store={store_param}put"

    url = f"http://10.10.90.233/23/api/?store=160put"

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    print(f"request: {data}")
    print(f"response url: {url}")
    print(f"Response: {response}")
    print("Status code:", response.status_code)

    try:
        response_json = response.json()
        bill_id = response_json.get("billId", "")
        sub_bill_id = response_json.get("subBillId", "")
        lottery = response_json.get("lottery", "")
        print(f"Reponse json: {response_json}")
    except Exception as e:
        print("⚠️ Failed to parse JSON response")
        print("Response text:", response.text)
        print("Error:", e)
        bill_id = ""
        sub_bill_id = ""
        lottery = ""

    # hervee status code 200 buyu amjilttai bolvol database-d hadgalna
    if response.status_code == 200:
        obj = Barimt.objects.create(
            billId=bill_id,
            subBillId=sub_bill_id,
            lottery=lottery,
            totalAmount=totalAmount,
            companyReg=company_reg_int,
            storeNo=store,
            created_by=request.user,
        )
        return JsonResponse(
            {
                "status": "success",
                "billId": bill_id,
                "subBillId": sub_bill_id,
                "lottery": lottery,
                "id": obj.id,
                "created_by": obj.created_by.username if obj.created_by else None,
            }
        )

    else:
        return JsonResponse(
            {"status": "failed",
             "message": "API call unsuccessful"},
            status=500
        )

# def barimt_list(request):
#     selected_date = request.GET.get("selected_date", "")
#     barimtuud = Barimt.objects.all().order_by("-id")
#     barimtuud_json = serializers.serialize("json", barimtuud)
#     page = request.GET.get("page", 1)
#     # if selected_date:
#     #     barimtuud = barimtuud.filter(created=selected_date)
#
#     paginator = Paginator(barimtuud, 20)  # нэг хуудсанд 20 мөр
#     barimtuud_page = paginator.get_page(page)
#
#     return render( request, "zasvarlah.html",
#         {
#             "barimtuud": barimtuud_page,
#             "barimtuud_json": barimtuud_json,
#             "page": barimtuud_page.number,
#             "total_pages": paginator.num_pages,
#             "has_prev": barimtuud_page.has_previous(),
#             "has_next": barimtuud_page.has_next(),
#             "selected_date": request.GET.get("selected_date", ""),
#         },
#     )

# excel file-aar tataj avah heseg
def export_excel(request):
    # jishee data (frontoos irsen ugugdliig ashiglana)
    amount = request.GET.get("amount")
    company_reg = request.GET.get("companyReg")
    store_no = request.GET.get("storeId")

    queryset = Barimt.objects.all()

    if amount:
        queryset = queryset.filter(totalAmount=amount)
    if company_reg:
        queryset = queryset.filter(companyReg=company_reg)
    if store_no:
        queryset = queryset.filter(storeId=store_no)

    # Хоосон байвал шууд мэдэгдэнэ
    if not queryset.exists():
        return JsonResponse(
            {"status": "failed", "message": "Мэдээлэл олдсонгүй"}, status=404
        )

    # DB-с ирсэн өгөгдлийг pandas DataFrame болгож хөрвүүлнэ
    data = []
    for obj in queryset:
        data.append(
            {
                "Нийт дүн": obj.totalAmount,
                "Сугалааны дугаар": obj.lottery,
                "billId": obj.billId,
                "subBillId": obj.subBillId,
                "Дэлгүүрийн дугаар": obj.storeNo,
                "Байгууллагын регистр": obj.companyReg,
                "Огноо": obj.created.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    df = pd.DataFrame(data)

    # Excel файл үүсгээд буцаана
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response[
        "Content-Disposition"
    ] = f'attachment; filename="barimt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Баримт")

    return response

def dashboard_view(request):
    selected_date = request.GET.get("selected_date")
    if not selected_date:
        yesterday = date.today() - timedelta(days=1)
        selected_date = yesterday.isoformat()

    page = int(request.GET.get("page", 1))

    api_url = "https://pp.cumongol.mn/api/bill/"
    payload = {"date": selected_date, "page": page}
    headers = {"Content-Type": "application/json"}

    barimtuud = []
    lottery_hooson_barimtuud = []
    has_prev = has_next = False
    total_pages = 1

    try:
        r = requests.post(
            api_url, json=payload, headers=headers, verify=False
        )  # verify=False SSL алдааас зайлсхийх
        r.raise_for_status()
        data = r.json()

        barimtuud = data.get("items", [])
        has_prev = data.get("has_prev", False)
        has_next = data.get("has_next", False)
        total_pages = data.get("total_pages", 1)

        # pos_api_bill_id хоосон баримтууд
        lottery_hooson_barimtuud = [
            b for b in barimtuud if not b.get("pos_api_bill_id")
        ]

    except Exception as e:
        print("API Error:", e)

    return render(
        request,
        "dashboard.html",
        {
            "selected_date": selected_date,
            "barimtuud": barimtuud,
            "lottery_hooson_barimtuud": lottery_hooson_barimtuud,
            "page": page,
            "has_prev": has_prev,
            "has_next": has_next,
            "total_pages": total_pages,
            "is_delete": True,
        },
    )

# API-аас баримт татаж, хадгалах функц
def fetch_and_save_barimt(status, date):
    token_url = "https://auth.itc.gov.mn/auth/realms/ITC/protocol/openid-connect/token"
    token_payload = {
        "client_id": "invoice",
        "grant_type": "password",
        "username": "ЖЮ00220821",
        "password": "Saiko@0208",
    }

    service_url = "https://api.ebarimt.mn/api/tpi/receipt/getSalesTotalData"

    attempts = 0
    max_retries = 50
    current_date = date
    while attempts < max_retries:
        try:
            token_response = requests.post(token_url, data=token_payload)
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")

            headers = {
                "x-api-key": "ae7368b03a55e135398668d964b5176e3e7f9c4f",
                "Authorization": f"Bearer {access_token}",
            }

            year, month, day = str(date.year), str(date.month), str(date.day)
            request_payload = {
                "year": year,
                "month": month,
                "day": day,
                "status": status,
                "startCount": 1,
                "endCount": 250000,
            }

            service_response = requests.post(
                service_url, headers=headers, json=request_payload
            )
            service_response.raise_for_status()
            data_list = service_response.json().get("data", {}).get("list", [])
        except HTTPError as e:
            print(f"HTTP алдаа: {e}")
            attempts += 1
            print(f"Оролдлого {attempts}/{max_retries}")

            if attempts >= max_retries:
                print(f"Хэт олон алдаа! Энэ өдрийг алгасна.")
                break

        except ValueError as e:
            print(f"JSON алдаа: {e}")
            break

        current_date += datetime.timedelta(days=1)
        print(f"\nДараагийн өдөр рүү шилжиж байна: {current_date}")

        # Моделд хадгалах
        if status == 0:
            model_class = Ebarimt_zadargaa_0
        else:
            model_class = Ebarimt_zadargaa_4

        objs = []
        for item in data_list:
            obj, _ = model_class.objects.update_or_create(
                posRno=item["posRno"], defaults=item
            )
            objs.append(obj)

        return objs
def compare_view(request):
    selected_date = request.GET.get("selected_date", None)
    check_total = request.GET.get("checkTotal")
    check_batch = request.GET.get("checkBatch")

    barimtuud = []

    # Огноогоор шүүх
    filters = {}
    if selected_date:
        filters["posRdate"] = selected_date
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

        # Нийт борлуулалтын баримт
        if check_total:
            barimtuud += fetch_and_save_barimt(status=0, date=date_obj)

        # Багцын толгой баримт
        if check_batch:
            barimtuud += fetch_and_save_barimt(status=4, date=date_obj)

    # Давхардалтыг арилгах (posRno-р ялгах)
    seen_posRno = set()
    unique_barimtuud = []
    for b in barimtuud:
        if b.posRno not in seen_posRno:
            unique_barimtuud.append(b)
            seen_posRno.add(b.posRno)

    context = {
        "barimtuud": unique_barimtuud,
        "selected_date": selected_date,
        "comparison_result": True,
    }
    return render(request, "tailan.html", context)

def user_groups(request):
    if request.user.is_authenticated:
        return {
            "is_hyanah": request.user.groups.filter(name="Hyanah").exists(),
            "is_zasvarlah": request.user.groups.filter(name="Zasvarlah").exists(),
            "is_tailan": request.user.groups.filter(name="Tailan").exists(),
            "is_delete": request.user.groups.filter(name="Delete").exists(),
        }
    return {}

@csrf_exempt
def delete_view(request):
    if request.method == "DELETE":
        data = json.loads(request.body)
        bill_id = data.get("billId")
        date = data.get("date")
        store_id = data.get("storeId")

        try:
            barimt = Barimt.objects.get(billId=bill_id, date=date, storeId=store_id)
            barimt.deleted_by = request.user  # 💡 Устгасан хэрэглэгчийг тэмдэглэх
            barimt.save()
            barimt.delete()
            return JsonResponse({"message": "Амжилттай устлаа"})
        except Barimt.DoesNotExist:
            return JsonResponse({"message": "Баримт олдсонгүй"}, status=404)

        # if request.method in ["POST", "DELETE"]:
        #     try:
        #         data = json.loads(request.body)
        #     except json.JSONDecodeError:
        #         return JsonResponse({"status": "error", "message": "JSON буруу байна."})
        #
        #     bill_id = data.get("billId")
        #     date = data.get("date")
        #     store = data.get("storeId")
        #
        #     store_str = str(store).lstrip('0') or '0'
        #     store_num = int(store_str)
        #     store_param = store_str
        #
        #     if not bill_id or not date or not store:
        #         return JsonResponse({"status": "error", "message": "Бүх талбар шаардлагатай."})

        base_ip = "10.10.90.234" if store_num >= 450 else "10.10.90.233"
        url = f"http://{base_ip}:9{store_param}/rest/receipt"

        print(url)

        payload = {"id": bill_id, "date": str(barimt.created_at)}
        resp = requests.delete(url, json=payload)

        print(resp.json())

        if resp.status_code == 200:
            return JsonResponse(
                {"status": "success", "message": "Баримт амжилттай устгагдлаа."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": f"API алдаа: {resp.status_code}"}
            )

    # GET хүсэлт → устгагдсан баримтуудыг render хийх
    selected_date = request.GET.get("selected_date")
    deleted_barimts = Barimt.objects.filter(is_deleted=True).order_by("-id")

    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            deleted_barimts = deleted_barimts.filter(
                created__gte=start_datetime, created__lt=end_datetime
            )
        except ValueError:
            pass

    return render(
        request,
        "delete.html",

        {"deleted_barimts": deleted_barimts, "selected_date": selected_date, "is_delete": True,},
    )

def aldaatai_barimt_oloh_view(request):
    if request.method == "GET":
        return render(request, "aldaatai_barimt.html")

def server_view(request):
    # servers = ServerStatus.objects.all().order_by('hostname')
    return render(request, 'server.html')
def nuhun_shiveh_view(request):
    if request.method == "GET":
        return render(request, "server.html")

#------------------------ AI model -----------------------------

def ebarimt_generate_with_ai(request):
    """
    AI шалгалттай баримт үүсгэх (Redis-гүй энгийн хувилбар)
    """
    try:
        # 1. Input авах
        total_amount = request.GET.get("totalAmount")
        company_reg = request.GET.get("companyId")
        store = request.GET.get("storeId")
        bill_type = request.GET.get("companyFieldTypeInput")

        if not total_amount or not store:
            return JsonResponse({
                "status": "error",
                "message": "Дүн болон дэлгүүрийн дугаар шаардлагатай"
            }, status=400)

        # 2. AI-аар шалгах
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""
Дараах баримтын мэдээллийг шалгаад JSON форматаар буцаа:

Өгөгдөл:
- Нийт дүн: {total_amount}
- Регистр: {company_reg or "байхгүй"}
- Дэлгүүр: {store}

Шалгах зүйлс:
1. Дүн сөрөг эсвэл 0 байж болохгүй
2. Дүн 100,000,000-с их байж болохгүй
3. Регистр байвал 7 оронтой эсэхийг шалга
4. Дэлгүүрийн дугаар зөв эсэхийг шалга

Заавал дараах JSON форматаар буцаа (бусад текст бичих хэрэггүй):
{{
    "is_valid": true немээс false,
    "errors": ["алдааны жагсаалт"],
    "suggestions": ["санал"],
    "validated_data": {{
        "totalAmount": "зассан дүн",
        "companyReg": "зассан регистр эсвэл null",
        "storeNo": "{store}",
        "billType": "{bill_type or ('1' if company_reg else '3')}"
    }}
}}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Та баримтын мэдээлэл шалгадаг AI туслах. Зөвхөн JSON буцаа."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # AI үр дүн авах
        ai_result = json.loads(response.choices[0].message.content)

        # 3. Алдаа байвал буцаах
        if not ai_result.get("is_valid", False):
            return JsonResponse({
                "status": "validation_failed",
                "errors": ai_result.get("errors", []),
                "suggestions": ai_result.get("suggestions", [])
            }, status=400)

        # 4. eBarimt API дуудах (таны одоогийн функц)
        validated_data = ai_result.get("validated_data", {})

        data = {
            "stocks": [{
                "measureUnit": "ширхэг",
                "code": "100541",
                "name": "Хүнсний бараа, ундаа, тамхины төрөлжсөн бус дэлгүүрийн жижиглэн худалдаа",
                "barCode": "6212",
                "qty": "1.00",
                "totalAmount": str(validated_data.get("totalAmount")),
                "cityTax": "0.00",
                "unitPrice": str(validated_data.get("totalAmount")),
                "vat": "1.00",
                "discount": "0.00",
            }],
            "transID": "11120035110134",
            "cashAmount": str(validated_data.get("totalAmount")),
            "nonCashAmount": "0.00",
            "amount": str(validated_data.get("totalAmount")),
            "cityTax": "0.00",
            "vat": "1.00",
            "billType": validated_data.get("billType"),
            "customerNo": str(validated_data.get("companyReg") or ""),
            "tenderType": "",
            "amountTendered": "0.00",
        }

        url = f"http://10.10.90.233/23/api/?store={store}put"
        headers = {"Content-Type": "application/json"}

        api_response = requests.post(url, headers=headers, data=json.dumps(data))

        # 5. Амжилттай бол Database-д хадгалах
        if api_response.status_code == 200:
            response_json = api_response.json()

            obj = Barimt.objects.create(
                billId=response_json.get("billId", ""),
                subBillId=response_json.get("subBillId", ""),
                lottery=response_json.get("lottery", ""),
                totalAmount=validated_data.get("totalAmount"),
                companyReg=validated_data.get("companyReg"),
                storeNo=store,
                created_by=request.user if request.user.is_authenticated else None,
            )

            return JsonResponse({
                "status": "success",
                "billId": obj.billId,
                "subBillId": obj.subBillId,
                "lottery": obj.lottery,
                "id": obj.id,
                "ai_validation": {
                    "is_valid": ai_result.get("is_valid"),
                    "suggestions": ai_result.get("suggestions", [])
                }
            })
        else:
            return JsonResponse({
                "status": "api_failed",
                "message": f"eBarimt API алдаа: {api_response.status_code}"
            }, status=500)

    except Exception as e:
        import traceback
        print("Алдаа:", traceback.format_exc())
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)