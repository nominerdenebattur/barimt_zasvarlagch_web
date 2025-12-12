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


class DownloadSchedule(models.Model):
    """Баримт татах хүсэлтийн хуваарь"""

    STATUS_CHOICES = [
        (0, 'Нийт борлуулалтын баримт'),
        (4, 'Багцын толгой баримт'),
    ]

    DOWNLOAD_STATUS_CHOICES = [
        ('pending', 'Хүлээгдэж байна'),
        ('processing', 'Татагдаж байна'),
        ('completed', 'Дууссан'),
        ('failed', 'Алдаа гарсан'),
        ('cancelled', 'Цуцлагдсан'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Хэрэглэгч',
        related_name='download_schedules'
    )
    start_date = models.DateField(verbose_name='Эхлэх огноо')
    end_date = models.DateField(verbose_name='Дуусах огноо')
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=4,
        verbose_name='Баримтын төрөл'
    )
    download_status = models.CharField(
        max_length=20,
        choices=DOWNLOAD_STATUS_CHOICES,
        default='pending',
        verbose_name='Таталтын төлөв'
    )

    # Үр дүн
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Файлын зам'
    )
    total_records = models.IntegerField(
        default=0,
        verbose_name='Нийт бичлэг'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Алдааны мэдээлэл'
    )

    # Огноо
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Үүсгэсэн огноо'
    )
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Эхэлсэн огноо'
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дууссан огноо'
    )

    class Meta:
        verbose_name = 'Таталтын хуваарь'
        verbose_name_plural = 'Таталтын хуваарьууд'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date}"

    def get_status_name(self):
        """Файлын нэрэнд ашиглах status нэр"""
        return 'niit_borluulalt' if self.status == 0 else 'bagtsiin_tolgoi'
