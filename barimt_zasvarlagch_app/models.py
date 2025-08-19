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

# class DeletedBarimt(models.Model):
#     billId = models.CharField(max_length=50)
#     subBillId = models.CharField(max_length=50, blank=True, null=True)
#     lottery = models.CharField(max_length=50, blank=True, null=True)
#     totalAmount = models.FloatField()
#     companyReg = models.CharField(max_length=50, blank=True, null=True)
#     storeNo = models.CharField(max_length=10)
#     deleted_by = models.CharField(max_length=250)
#     deleted_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.billId} - {self.deleted_by}"