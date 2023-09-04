from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import FirstMarket, EditModeMessages, DeleteMarket, ManualCallback, \
    EmptyTextCallback, EditEmptyTextCallback


async def main_menu_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔐 Личный кабинет", callback_data="my_office")
    keyboard.button(text="✍️ Создать ответ в ручную", callback_data="create_anw")
    keyboard.button(text="📘 Инструкция", callback_data="instruction")
    keyboard.button(text="✉️ Обратная связь", url="https://t.me/smart_support_auto")
    return keyboard.adjust(1).as_markup()


async def back_menu_bot_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data='back_to_menu')
    return keyboard.adjust(1).as_markup()


async def first_show_bot_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Ознакомился!", callback_data='back_to_menu')
    return keyboard.adjust(1).as_markup()


async def gen_again_kb(feed):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🔄 Сгенерировать ответ заново', callback_data=ManualCallback(id=feed.pk))
    return keyboard.as_markup()


async def back_to_main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена', callback_data='back_to_menu')
    return keyboard.as_markup()


async def myself_office_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🏢 Мои кабинеты', callback_data='my_cabinets')
    kb.button(text='⏰ Время отправки уведомлений', callback_data='time_send_feed')
    kb.button(text='📊 Статистика', callback_data='statistic')
    kb.button(text='🖋 Подпись к ответам', callback_data='sig_answers')
    kb.button(text='🔔 Настроить уведомления', callback_data='sett_feed')
    kb.button(text='🔙 Назад', callback_data='back_to_menu')
    kb.adjust(1)
    return kb.as_markup()


async def add_office_kb(cabinets):
    kb = InlineKeyboardBuilder()
    for cabinet in cabinets:
        kb.button(text=cabinet.name_market, callback_data=FirstMarket(id=cabinet.pk))
    if cabinets.count() <= 4:
        kb.button(text='➕ Добавить магазин', callback_data='add_token')
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def cancel_add_token():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data='my_cabinets')
    return kb.as_markup()


async def check_setting_market(market):
    kb = InlineKeyboardBuilder()
    kb.button(text='🔍 Проверить настройки магазина', callback_data=FirstMarket(id=market.pk))
    return kb.as_markup()


async def adit_mode_messages(market):
    kb = InlineKeyboardBuilder()
    kb.button(text='🤖 Все в автоматическом режиме', callback_data=EditModeMessages(id=market.pk, mode_mes='auto'))
    kb.button(text='⚙️ Все в полуавтоматическом режиме',
              callback_data=EditModeMessages(id=market.pk, mode_mes='not_auto'))
    kb.button(text='📝 Ответ на отзывы без текста', callback_data=EmptyTextCallback(id=market.pk))
    kb.button(text='🗑 Удалить магазин', callback_data=DeleteMarket(id=market.pk))
    kb.button(text='🏢 Мои кабинеты', callback_data='my_cabinets')
    kb.adjust(1)
    return kb.as_markup()


async def cancel_enter_stars_state():
    kb = InlineKeyboardBuilder()
    kb.button(text='❌ Отмена', callback_data='stop_star')
    return kb.as_markup()


async def delete_market_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='✔️ Да', callback_data='yes_del')
    kb.button(text='✖️ Нет', callback_data='my_cabinets')
    return kb.as_markup()


async def answer_to_empty_kb(mode):
    kb = InlineKeyboardBuilder()
    if mode.send_empty_text:
        kb.button(text='❌ Не отвечать', callback_data=EditEmptyTextCallback(id=mode.pk, mode='stop_answer'))
    else:
        kb.button(text='✅ Отвечать', callback_data=EditEmptyTextCallback(id=mode.pk, mode='ok_answer'))
    row = InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_call')
    row2 = InlineKeyboardButton(text='🏢 Мои кабинеты', callback_data='my_cabinets')
    return kb.adjust(1).row(row, row2).as_markup()
