# Generated by Django 4.2 on 2023-09-04 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telebot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wbtoken',
            name='send_empty_text',
            field=models.BooleanField(default=True, verbose_name='Ответ на отзывы без текста'),
        ),
    ]
