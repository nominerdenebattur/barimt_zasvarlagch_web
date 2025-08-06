from django.db import models

class Barimt(models.Model):
    totalAmount = models.FloatField(default=0)
    lottery = models.CharField(max_length=10 , blank = True, default="0")
    billId = models.CharField(max_length=50, default="0")
    subBillId = models.CharField(max_length=50, default="0")
    storeId = models.CharField(max_length=5, default="0")
    companyId = models.IntegerField(default=0)
