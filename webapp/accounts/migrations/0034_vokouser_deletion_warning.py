from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0033_userprofile_orderround_mail_optout"),
    ]

    operations = [
        migrations.AddField(
            model_name="vokouser",
            name="deletion_warning_sent",
            field=models.DateTimeField(
                blank=True, null=True, help_text="When deletion warning email was sent to this member"
            ),
        ),
        migrations.AddField(
            model_name="vokouser",
            name="deletion_token",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                help_text="Token used in deletion warning email link",
            ),
        ),
    ]
