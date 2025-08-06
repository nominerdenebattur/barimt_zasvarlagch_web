import os
import pandas as pd

from django.contrib.sites import requests
from django.shortcuts import render
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.datetime_safe import datetime
from .models import Barimt

def zasvarlah(request):
    return render(request, 'zasvarlah.html')

def ebarimt_generate(request):
    # === Input Data ===
    totalAmount = request.GET.get('totalAmount')
    regNo = request.GET.get('companyId')
    store = request.GET.get('storeId')

    vat = "1.00"
    cashAmount = totalAmount
    nonCashAmount = "0.00"
    amount = totalAmount
    cityTax = "0.00"
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
        url = f"http://10.10.90.233/23/api/?store={store_param}"
    else:
        url = f"http://10.10.90.234/23/api/?store={store_param}"

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    print("Status code:", response.status_code)

    # === Excel Log ===
    log_file = "api_post_log.xlsx"
    today = datetime.today().strftime("%Y-%m-%d")

    try:
        response_json = response.json()
        bill_id = response_json.get("billId", "")
        sub_bill_id = response_json.get("subBillId", "")
    except Exception:
        bill_id = ""
        sub_bill_id = ""
        print("⚠️ Failed to parse JSON response")

    # Prepare log row
    log_row = {
        "date": today,
        "amount": totalAmount,
        "billId": bill_id,
        "subBillId": sub_bill_id
    }

    # Append to Excel
    if os.path.exists(log_file):
        df = pd.read_excel(log_file)
        df = pd.concat([df, pd.DataFrame([log_row])], ignore_index=True)
    else:
        df = pd.DataFrame([log_row])

    df.to_excel(log_file, index=False)
    print(f"✅ Excel log updated: {log_file}")