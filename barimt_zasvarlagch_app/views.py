import os
import pandas as pd
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils.datetime_safe import datetime
from .models import Barimt


from datetime import datetime, timedelta

def zasvarlah(request):
    selected_date = request.GET.get('selected_date')
    barimtuud = Barimt.objects.all().order_by('-created')

    if selected_date:
        try:
            # selected_date-г datetime.date болгож хөрвүүлэх
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

            # Өдрийн эхлэл ба дараагийн өдрийн эхлэл
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)

            # Огноо, цагийн хүрээнд шүүх
            barimtuud = barimtuud.filter(created__gte=start_datetime, created__lt=end_datetime)
        except ValueError:
            pass

    return render(request, 'zasvarlah.html', {
        'barimtuud': barimtuud,
        'selected_date': selected_date
    })


def ebarimt_generate(request):
    # === Input Data ===
    totalAmount = request.GET.get('totalAmount')
    regNo = request.GET.get('companyId')
    company_reg_int = str(regNo) if regNo else None

    # if regNo:
    #     billType = 1
    # else:
    #     billType = 3
    store = request.GET.get('storeId')

    vat = "1.00"
    cashAmount = totalAmount
    nonCashAmount = "0.00"
    amount = totalAmount
    cityTax = "0.00"
    billType = request.GET.get('companyFieldTypeInput')

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
                "discount": "0.00"
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
        "amountTenderedCoupon": "0.00"
    }

    store_str = str(store).lstrip('0') or '0'
    store_num = int(store_str)
    store_param = store_str

    if store_num > 450:
        url = f"http://10.10.90.234/23/api/?store={store_param}put"
    else:
        url = f"http://10.10.90.233/23/api/?store={store_param}put"

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
            storeNo=store
        )
        return JsonResponse({
            "status": "success",
            "billId": bill_id,
            "subBillId": sub_bill_id,
            "lottery": lottery,
            "id": obj.id
        })

    else:
        return JsonResponse({"status": "failed", "message": "API call unsuccessful"}, status=500)


# excel file-aar tataj avah heseg
def export_excel(request):
    # jishee data (frontoos irsen ugugdliig ashiglana)
    amount = request.GET.get('amount')
    company_reg = request.GET.get('companyReg')
    store_no = request.GET.get('storeId')

    queryset = Barimt.objects.all()

    if amount:
        queryset = queryset.filter(totalAmount=amount)
    if company_reg:
        queryset = queryset.filter(companyReg=company_reg)
    if store_no:
        queryset = queryset.filter(storeId=store_no)

    # Хоосон байвал шууд мэдэгдэнэ
    if not queryset.exists():
        return JsonResponse({"status": "failed", "message": "Мэдээлэл олдсонгүй"}, status=404)

    # DB-с ирсэн өгөгдлийг pandas DataFrame болгож хөрвүүлнэ
    data = []
    for obj in queryset:
        data.append({
            "Нийт дүн": obj.totalAmount,
            "Сугалааны дугаар": obj.lottery,
            "billId": obj.billId,
            "subBillId": obj.subBillId,
            "Дэлгүүрийн дугаар": obj.storeNo,
            "Байгууллагын регистр": obj.companyReg,
            "Огноо": obj.created.strftime('%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(data)

    # Excel файл үүсгээд буцаана
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="barimt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Баримт')

    return response