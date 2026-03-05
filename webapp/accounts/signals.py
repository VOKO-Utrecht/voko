from django.apps import apps
from django.core.mail import mail_admins, send_mail
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(pre_save, sender="accounts.VokoUser")
def handle_member_set_to_sleeping(sender, instance, **kwargs):
    """When a member is set to sleeping, remove them from future shifts/rides and notify coordinators."""
    if instance.pk is None:
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if previous.is_asleep or not instance.is_asleep:
        return

    _remove_from_future_shifts(instance)
    _notify_about_future_rides(instance)


def _remove_from_future_shifts(user):
    Shift = apps.get_model("distribution", "Shift")
    future_shifts = Shift.objects.filter(
        members=user,
        order_round__collect_datetime__gte=timezone.now(),
    )

    for shift in future_shifts:
        coordinator = shift.distribution_coordinator
        shift.members.remove(user)
        _notify_coordinator_about_shift(coordinator, user, shift)


def _notify_coordinator_about_shift(coordinator, user, shift):
    subject = f"Lid {user.get_full_name()} is op slaapstand gezet en verwijderd uit uitdeeldienst"
    message = (
        f"Lid {user.get_full_name()} is op slaapstand gezet.\n\n"
        f"Dit lid is verwijderd uit de uitdeeldienst op {shift.date_long_str} "
        f"({shift.start_str} - {shift.end_str}).\n\n"
        f"Gelieve een vervanger te regelen."
    )

    if coordinator:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[coordinator.email],
            fail_silently=True,
        )
    else:
        mail_admins(subject, message, fail_silently=True)


def _notify_about_future_rides(user):
    Ride = apps.get_model("transport", "Ride")
    future_rides = Ride.objects.filter(
        Q(driver_id=user.pk) | Q(codriver_id=user.pk),
        order_round__collect_datetime__gte=timezone.now(),
    )

    for ride in future_rides:
        coordinator = ride.transport_coordinator
        _notify_coordinator_about_ride(coordinator, user, ride)


def _notify_coordinator_about_ride(coordinator, user, ride):
    subject = f"Lid {user.get_full_name()} is op slaapstand gezet en ingepland voor transportdienst"
    message = (
        f"Lid {user.get_full_name()} is op slaapstand gezet.\n\n"
        f"Dit lid staat ingepland voor de transportdienst op {ride.date_str} "
        f"(route: {ride.route}).\n\n"
        f"Gelieve een vervanger te regelen."
    )

    if coordinator:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[coordinator.email],
            fail_silently=True,
        )
    else:
        mail_admins(subject, message, fail_silently=True)
