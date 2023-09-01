from django.contrib import admin
from django.contrib.admin import AdminSite, ModelAdmin
from django.utils.html import format_html

from admin_panel.telebot.models import Client


class BotAdminSite(AdminSite):
    site_title = "Управление ботом"
    site_header = "Управление ботом"
    index_title = ""


bot_admin = BotAdminSite()


@admin.register(Client, site=bot_admin)
class ClientAdmin(ModelAdmin):
    list_display = (
        'pk',
        'name',
        'user_link',
        'username',
        'telegram_id',
        'created'
    )
    list_display_links = ('pk', 'username')
    empty_value_display = '-пусто-'
    search_fields = ('username', 'telegram_id')

    def user_link(self, object: Client):
        if object.username and object.name:
            return format_html('<a href="https://t.me/{}">{}</a>', object.username, object.name)
        else:
            return object.url

    user_link.short_description = "Ссылка"

    class Meta:
        verbose_name_plural = 'Клиенты бота'
