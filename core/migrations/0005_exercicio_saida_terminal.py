# Generated by Django 3.0.3 on 2020-06-04 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_respostaexprogramacao_stdouts'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercicio',
            name='saida_terminal',
            field=models.BooleanField(default=True),
        ),
    ]
