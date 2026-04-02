from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User


@receiver(post_save, sender=User)
def sync_flags(sender, instance, **kwargs):
    if instance.role == User.ADMIN:
        User.objects.filter(pk=instance.pk).update(
            # is_active=True,
            is_staff=True,
            is_superuser=True,
        )

    elif instance.role == User.SUPERVISOR:
        User.objects.filter(pk=instance.pk).update(
            # is_active=True,
            is_staff=True,
            is_superuser=False,
        )

    elif instance.role == User.PRODUCTOR:
        User.objects.filter(pk=instance.pk).update(
            # is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        
    def apply_groups():
        group_supervisor, _ = Group.objects.get_or_create(name="Supervisor")
        group_productor, _ = Group.objects.get_or_create(name="Productor")

        if instance.role == User.SUPERVISOR:
            instance.groups.remove(group_productor)
            instance.groups.add(group_supervisor)

        elif instance.role == User.PRODUCTOR:
            instance.groups.remove(group_supervisor)
            instance.groups.add(group_productor)

        elif instance.role == User.ADMIN:
            instance.groups.clear()

    transaction.on_commit(apply_groups)
