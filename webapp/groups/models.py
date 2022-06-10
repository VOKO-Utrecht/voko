from django.db import models


class GroupExt(models.Model):

    # Extending Groups

    class Meta:
        verbose_name = "groep extentie"

    def __str__(self):
        return "{}".format(self.group.name)

    group = models.OneToOneField('auth.Group', unique=True, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, blank=True, default="")
