from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import DatesCallback, MyMarkets
from tgbot.misc.some_data import date_dct


async def show_time_kb(date_list, dates):
    kb = InlineKeyboardBuilder()
    if date_list[0] == 'my_time':
        kb.button(text='✅️ Мое время', callback_data=DatesCallback(date='my_time'))
    for date in dates:
        text = '✅️ ' + date_dct().get(date) if date in date_list else date_dct().get(date)
        kb.button(text=text, callback_data=DatesCallback(date=date))
    kb.button(text="Ввести самостоятельно", callback_data='enter_self')
    kb.button(text="Назад", callback_data='my_office')
    return kb.adjust(1).as_markup()


async def days_statistic():
    kb = InlineKeyboardBuilder()
    kb.button(text='📅 За сегодня', callback_data='stat_today')
    kb.button(text='📅 За вчера', callback_data='stat_last_day')
    kb.button(text='📅 За неделю', callback_data='stat_week')
    kb.button(text='📅 За последние 30 дней', callback_data='last_30')
    kb.button(text="🔙 Назад", callback_data='my_office')
    return kb.adjust(1).as_markup()


async def back_stat():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data='statistic')
    return kb.adjust(1).as_markup()


async def markets_kb(cabinets):
    kb = InlineKeyboardBuilder()
    for cabinet in cabinets:
        kb.button(text=cabinet.name_market, callback_data=MyMarkets(id=cabinet.pk))
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def edit_signature_kb(market):
    kb = InlineKeyboardBuilder()
    if market:
        kb.button(text='✒️  Изменить подпись', callback_data='edit_signature')
    else:
        kb.button(text='➕ Добавить подпись', callback_data='add_signature')
    kb.button(text="🔙 Назад", callback_data='sig_answers')
    return kb.adjust(1).as_markup()


async def cancel_add_signature():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data='sig_answers')
    return kb.adjust(1).as_markup()


# async def check_signature_kb():
#     kb = InlineKeyboardBuilder()
#     kb.button(text="Проверить подпись", callback_data='sig_answers')
#     return kb.adjust(1).as_markup()


async def feedback_choose_action_kb(feedback):
    kb = InlineKeyboardBuilder()
    if feedback:
        kb.button(text='❌ Отключить уведомления', callback_data='feed_true')
    else:
        kb.button(text='✅ Включить уведомления', callback_data='feed_false')
    kb.button(text="Назад", callback_data='my_office')
    return kb.adjust(1).as_markup()
