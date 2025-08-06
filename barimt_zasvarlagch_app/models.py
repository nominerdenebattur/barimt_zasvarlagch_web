from django.db import models

class Barimt(models.Model):
    amount = models.FloatField()
    lottery = models.CharField(max_length=10)
    subBillId = models.IntegerField()
    storeId = models.IntegerField()
    companyId = models.IntegerField()
