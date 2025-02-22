# Generated by Django 4.2 on 2023-09-04 11:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telebot', '0002_wbtoken_send_empty_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncorrectWbToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=150, verbose_name='Токен WB пользователя')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inc_wb_token', to='telebot.client', verbose_name='Токен WB')),
            ],
        ),
    ]
