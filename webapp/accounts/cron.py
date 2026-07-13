from datetime import timedelta
from uuid import uuid4

from constance import config
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_cron import CronJobBase, Schedule

from accounts.models import VokoUser
from mailing.helpers import get_template_by_id, mail_user, render_mail_template


class WarnDormantMembers(CronJobBase):
    """
    Sends a warning email to members who have been inactive for 1 year.

    Cron runs every 24 hours.

    Targets active members where last_login (or activated date as fallback)
    is more than 1 year ago and no deletion warning has been sent yet.
    The email contains a link the member can click to cancel their deletion.
    Template: SLEEPING_MEMBER_WARNING_MAIL
    """

    RUN_EVERY_MINS = 60 * 24

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "accounts.warn_dormant_members"

    def do(self):
        one_year_ago = timezone.now() - timedelta(days=365)

        dormant_members = VokoUser.objects.filter(
            is_active=True,
            deletion_warning_sent__isnull=True,
        ).filter(
            Q(last_login__lt=one_year_ago) | Q(last_login__isnull=True, activated__lt=one_year_ago)
        )

        print(f"WarnDormantMembers: found {dormant_members.count()} dormant member(s)")

        mail_template = get_template_by_id(config.SLEEPING_MEMBER_WARNING_MAIL)

        for user in dormant_members:
            token = str(uuid4())
            user.deletion_token = token
            user.deletion_warning_sent = timezone.now()
            user.save()

            cancel_url = settings.BASE_URL + reverse("cancel_deletion", args=(token,))
            rendered = render_mail_template(mail_template, user=user, url=cancel_url)
            mail_user(user, *rendered)
            print(f"Sent deletion warning to {user.email}")


class DeleteDormantMembers(CronJobBase):
    """
    Deletes members who did not respond to the deletion warning within 1 week.

    Cron runs every 24 hours.
    """

    RUN_EVERY_MINS = 60 * 24

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "accounts.delete_dormant_members"

    def do(self):
        one_week_ago = timezone.now() - timedelta(weeks=1)

        members_to_delete = VokoUser.objects.filter(
            deletion_warning_sent__lt=one_week_ago,
        )

        print(f"DeleteDormantMembers: found {members_to_delete.count()} member(s) to delete")

        for user in members_to_delete:
            print(f"Deleting dormant member: {user.email}")
            user.delete()
