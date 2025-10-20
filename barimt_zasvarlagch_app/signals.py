from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Barimt

@receiver(post_save, sender=Barimt)
def log_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    ActivityLog.objects.create(
        user=getattr(instance, "modified_by", None),
        action=action,
        model="Barimt",
        object_id=instance.id #yamar mur nemegdseniig todorhoilhod hereglene
    )

@receiver(post_delete, sender=Barimt)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        user=getattr(instance, "modified_by", None),
        action="deleted",
        model="Barimt",
        object_id=instance.id
    )