# Generated by Django 3.2.18 on 2023-08-14 07:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_alter_publishevent_unique_together'),
        ('plugin', '0006_auto_20230620_1512'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pluginbinding',
            old_name='api',
            new_name='gateway',
        ),
        migrations.RenameField(
            model_name='pluginconfig',
            old_name='api',
            new_name='gateway',
        ),
        migrations.AlterField(
            model_name='pluginbinding',
            name='gateway',
            field=models.ForeignKey(db_column='api_id', on_delete=django.db.models.deletion.CASCADE, to='core.gateway'),
        ),
        migrations.AlterField(
            model_name='pluginconfig',
            name='gateway',
            field=models.ForeignKey(db_column='api_id', on_delete=django.db.models.deletion.CASCADE, to='core.gateway'),
        ),
        migrations.AlterUniqueTogether(
            name='pluginconfig',
            unique_together=set(),
        ),
    ]
