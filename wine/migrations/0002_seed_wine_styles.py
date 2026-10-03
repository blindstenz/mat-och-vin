from django.db import migrations


def seed(apps, schema_editor):
    from wine.styles_data import sync_styles

    sync_styles(apps.get_model("wine", "WineStyle"))


class Migration(migrations.Migration):
    dependencies = [("wine", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
