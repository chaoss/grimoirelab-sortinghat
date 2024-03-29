# Generated by Django 3.2.23 on 2024-02-13 11:17

from django.db import migrations, models
import django.db.models.deletion
import grimoirelab_toolkit.datetime
import sortinghat.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_delete_importidentitiestask'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', sortinghat.core.models.CreationDateTimeField(default=grimoirelab_toolkit.datetime.datetime_utcnow, editable=False)),
                ('last_modified', sortinghat.core.models.LastModificationDateTimeField(default=grimoirelab_toolkit.datetime.datetime_utcnow, editable=False)),
                ('alias', models.CharField(max_length=128)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='core.group')),
            ],
            options={
                'db_table': 'aliases_organizations',
                'ordering': ('alias',),
                'unique_together': {('alias',)},
            },
        ),
    ]
