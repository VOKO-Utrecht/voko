from .models import EventLog


def log_event(operator=None,
              user=None,
              event="",
              extra=None):
    EventLog.objects.create(operator=operator,
                            user=user,
                            event=event,
                            extra=extra)
