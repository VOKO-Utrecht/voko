

def log_event(operator=None,
              user=None,
              event="",
              extra=None):

    from models import EventLog

    EventLog.objects.create(operator=operator,
                            user=user,
                            event=event,
                            extra=extra)
