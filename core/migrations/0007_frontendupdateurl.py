# Generated by Django 3.1.3 on 2022-07-12 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_semester'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrontendUpdateUrl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024)),
                ('url', models.URLField()),
            ],
        ),
    ]
