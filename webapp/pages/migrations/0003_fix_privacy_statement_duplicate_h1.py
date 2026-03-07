from django.db import migrations


def remove_duplicate_h1(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    try:
        page = Page.objects.get(slug="privacy-statement")
    except Page.DoesNotExist:
        return
    page.content = page.content.replace("<h1>Privacy statement VOKO Utrecht</h1>\n", "", 1)
    page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0002_seed_privacy_statement"),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_h1, migrations.RunPython.noop),
    ]
