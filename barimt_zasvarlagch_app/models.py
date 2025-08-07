from django.db import models

class Barimt(models.Model):
    totalAmount = models.FloatField(default=0)
    lottery = models.CharField(max_length=10 , blank = True, default="0")
    billId = models.CharField(max_length=50, default="0")
    subBillId = models.CharField(max_length=50, default="0")
    storeId = models.CharField(max_length=5, default="0")
    #companyId -> companyReg
    companyReg = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


    # ?
    def __str__(self):
        return f"{self.billId or 'NoBill'} - {self.totalAmount}"

