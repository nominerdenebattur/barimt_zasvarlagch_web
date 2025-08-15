from django.db import models
from django.utils import timezone


class Barimt(models.Model):
    totalAmount = models.FloatField(default=0)
    lottery = models.CharField(max_length=20, blank=True, default="0")
    billId = models.CharField(max_length=50, default="0")
    subBillId = models.CharField(max_length=50, default="0")
    storeNo = models.CharField(max_length=5, default="0")
    companyReg = models.CharField(default=0, blank=True, null=True, max_length=10)
    created = models.DateTimeField(default=timezone.now)

    # ?
    def __str__(self):
        return f"{self.billId or 'NoBill'} - {self.totalAmount}"
