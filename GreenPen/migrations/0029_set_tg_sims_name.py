# Generated by Django 3.1.5 on 2021-02-15 09:09

from django.db import migrations
# from GreenPen.models import TeachingGroup

def set_sims_tg_name(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    TeachingGroup = apps.get_model("GreenPen", "TeachingGroup")
    for tg in TeachingGroup.objects.all():
        tg.sims_name = tg.name
        tg.save()

class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0028_teachinggroup_sims_name'),
    ]

    operations = [
        migrations.RunPython(set_sims_tg_name)
    ]
