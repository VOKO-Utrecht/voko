from django.db import DatabaseError
from django_cron import CronJobBase, Schedule
from django.db.models import Q
import log
from datetime import datetime, timedelta
from accounts.models import SleepingVokoUser, VokoUser


class DeleteInactiveAccounts(CronJobBase):
    """
    Deletes (older) accounts that were never activated

    cron runs every day

    """

    RUN_EVERY_MINS = 60 * 24
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "accounts.delete_inactive_accounts"

    def delete_inactive_users(self, model):
        six_months_ago = datetime.now() - timedelta(weeks=26)
        inactive_users = model.objects.filter(Q(created__lt=six_months_ago) & Q(can_activate=False))

        # Delete users one by one to prevent a single failure to stop the entire transaction
        for user in inactive_users:
            try:
                log.log_event(user=user, event=f"Deleting inactive useraccount {user.id}")
                model.delete(user)
            except DatabaseError as e:
                log.log_event(user=user, event=f"Could not delete inactive useraccount {user.id}", extra=str(e))

    def do(self):
        for model in (VokoUser, SleepingVokoUser):
            self.delete_inactive_users(model)
