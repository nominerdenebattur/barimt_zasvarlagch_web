from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Barimt

def create_groups_permissions(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(Barimt)
    # Groups үүсгэх
    hyanh_group, created = Group.objects.get_or_create(name='Hyanah')
    zasvarlah_group, created = Group.objects.get_or_create(name='Zasvarlah')
    tailan_group, created = Group.objects.get_or_create(name='Tailan')

    # Barimt model-ийн default permission авах
    content_type = ContentType.objects.get_for_model(Barimt)

    # View permission (Dashboard-д хэрэглэгдэнэ)
    view_barimt_perm = Permission.objects.get(codename='view_barimt', content_type=content_type)
    hyanh_group.permissions.add(view_barimt_perm)

    # Засварлах permission
    change_barimt_perm = Permission.objects.get(codename='change_barimt', content_type=content_type)
    zasvarlah_group.permissions.add(change_barimt_perm)

    # Тайлан permission (жишээ нь view_barimt ашиглаж болно)
    tailan_barimt_perm = Permission.objects.get(codename='change_barimt', content_type=content_type)
    tailan_group.permissions.add(tailan_barimt_perm)
