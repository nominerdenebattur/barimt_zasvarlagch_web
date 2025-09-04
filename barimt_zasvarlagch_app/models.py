from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Barimt(models.Model):
    totalAmount = models.FloatField(default=0)
    lottery = models.CharField(max_length=20, blank=True, default="0")
    billId = models.CharField(max_length=50, default="0")
    subBillId = models.CharField(max_length=50, default="0")
    storeNo = models.CharField(max_length=5, default="0")
    companyReg = models.CharField(default=0, blank=True, null=True, max_length=10)
    created = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)
    # Хэрэглэгчийн талаарх нэмэлт талбар
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="barimt_created")
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="barimt_deleted")
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self, user):
        self.is_deleted = True
        self.deleted_by = user
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.billId or 'NoBill'} - {self.totalAmount}"

User = get_user_model()

class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class Ebarimt_zadargaa_0(models.Model):
    posSid = models.CharField(default=0, blank=True, null=True, max_length=500)
    posRno = models.CharField(default=0, blank=True, null=True, max_length=500)
    posRdate = models.CharField(default=0, blank=True, null=True, max_length=500)
    posRamt = models.IntegerField(default=0)
    citytax = models.IntegerField(default=0)
    posVamt = models.IntegerField(default=0)
    netAmt = models.IntegerField(default=0)
    fromType = models.CharField(default=0, blank=True, null=True, max_length=500)
    csmrRegNo = models.CharField(default=0, blank=True, null=True, max_length=500)
    csmrName = models.CharField(default=0, blank=True, null=True, max_length=500)
    posNo = models.IntegerField(default=0)
    operatorName = models.CharField(default=0, blank=True, null=True, max_length=10)
    districtCode = models.CharField(default=0, blank=True, null=True, max_length=10)
    prParentRno = models.CharField(default=0, blank=True, null=True, max_length=10)

    def __str__(self):
        return self.posRno

class Ebarimt_zadargaa_4(models.Model):
        posSid = models.CharField(default=0, blank=True, null=True, max_length=10)
        posRno = models.CharField(default=0, blank=True, null=True, max_length=10)
        posRdate = models.CharField(default=0, blank=True, null=True, max_length=10)
        posRamt = models.IntegerField(default=0)
        citytax = models.IntegerField(default=0)
        posVamt = models.IntegerField(default=0)
        netAmt = models.IntegerField(default=0)
        fromType = models.CharField(default=0, blank=True, null=True, max_length=10)
        csmrRegNo = models.CharField(default=0, blank=True, null=True, max_length=10)
        csmrName = models.CharField(default=0, blank=True, null=True, max_length=10)
        posNo = models.IntegerField(default=0)
        operatorName = models.CharField(default=0, blank=True, null=True, max_length=10)
        districtCode = models.CharField(default=0, blank=True, null=True, max_length=10)
        prParentRno = models.CharField(default=0, blank=True, null=True, max_length=10)

        def __str__(self):
            return self.posRno