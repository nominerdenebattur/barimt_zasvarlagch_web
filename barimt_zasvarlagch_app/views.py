import os
import pandas as pd
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils.datetime_safe import datetime
from .models import Barimt

def zasvarlah(request):
    return render(request, 'zasvarlah.html')


def ebarimt_generate(request):
    # === Input Data ===
    totalAmount = request.GET.get('totalAmount')
    #companyId?
    regNo = request.GET.get('companyId')
    store = request.GET.get('storeId')

    vat = "1.00"
    cashAmount = totalAmount
    nonCashAmount = "0.00"
    amount = totalAmount
    cityTax = "0.00"
    #aldaa billType aa bas avtomataar avna
    billType = "1"

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

    store_param = f"{store}put"
    store_str = str(store).lstrip('0') or '0'
    store_num = int(store_str)

    if store_num > 450:
        url = f"http://10.10.90.234/23/api/?store={store_param}"
    else:
        url = f"http://10.10.90.233/23/api/?store={store_param}"

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    #print("Status code:", response.status_code)


    today = datetime.today().strftime("%Y-%m-%d")

    try:
        response_json = response.json()
        bill_id = response_json.get("billId", "")
        sub_bill_id = response_json.get("subBillId", "")
    except Exception:
        bill_id = ""
        sub_bill_id = ""
        print("⚠️ Failed to parse JSON response")


    # hervee status code 200 buyu amjilttai bolvol database-d hadgalna
    if response.status_code == 200:
        obj = Barimt.objects.create(
            billId=bill_id,
            subBillId=sub_bill_id,
            #html-s importloh?
            lottery=lottery,
            totalAmount=totalAmount,
            companyId=int(regNo),
            storeId=store
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

#excel file-aar tataj avah heseg
def export_excel(request):
    # jishee data (frontoos irsen ugugdliig ashiglana)
    amount = request.GET.get('amount', '0')
    company_reg = request.GET.get('companyReg', '-')
    store_no = request.GET.get('storeId', '-')

    # DataFrame bolgij excel filed bichih
    df = pd.DataFrame([{
        "Нийт дүн": amount,
        "Сугалааны дугаар": "TEST12345",
        "billId": "BILL001",
        "subBillId": "SUB001",
        "Дэлгүүрийн дугаар": store_no,
        "Байгууллагын регистр": company_reg
    }])

    # HTTP hariug excel bolgon butsaah
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="barimt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    # pandas аshiglaj Excel ruu shuud bichih
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Баримт')

    return response

