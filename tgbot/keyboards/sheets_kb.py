from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import EditMode, MarketsTables, TriggerPagCallback, TriggerPagenCallback


async def add_market_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Подключить магазин', callback_data='my_cabinets')
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def menu_sheet_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🗂 Мои таблицы', callback_data='my_sheets')
    kb.button(text='➕ Добавить таблицу', callback_data='add_sheet')
    kb.button(text='💤 Неотвеченные отзывы', callback_data='wait_answer')
    kb.button(text='📘 Инструкция', callback_data='instruct_sheet')
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def edit_sheet_mode_kb(market):
    kb = InlineKeyboardBuilder()
    if not market.use_sheet:
        kb.button(text='Исп. таблицы', callback_data=EditMode(id=market.pk, mode='use_sheet'))
    else:
        kb.button(text='Исп. GPT', callback_data=EditMode(id=market.pk, mode='not_use_sheet'))
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def markets_all_kb(markets):
    kb = InlineKeyboardBuilder()
    for market in markets:
        if not market.gmail_markets.first():
            kb.button(text=market.name_market, callback_data=MarketsTables(id=market.pk))
    kb.button(text='🔙 Назад', callback_data='table_sheet')
    return kb.adjust(1).as_markup()


async def cancel_add_url(text):
    kb = InlineKeyboardBuilder()
    kb.button(text=text, callback_data='add_sheet')
    return kb.adjust(1).as_markup()


async def markets_url(markets):
    kb = InlineKeyboardBuilder()
    for market in markets:
        kb.button(text=market.market.name_market, url=market.url)
    kb.button(text='🔙 Назад', callback_data='table_sheet')
    return kb.adjust(1).as_markup()


async def type_feeds_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='Триггеры', callback_data='trig_wait')
    kb.button(text='Без триггеров', callback_data='no_trig_wait')
    kb.button(text='🔙 Назад', callback_data='table_sheet')
    return kb.adjust(1).as_markup()


async def pagen_triggers(triggers, start: int, stop: int):
    builder = InlineKeyboardBuilder()
    if start < 0:
        start = 0
        stop = 6
    elif start > len(triggers) - 1:
        start = 0
        stop = 6
    for trigger in triggers[start:stop]:
        builder.button(text=trigger.category_name, callback_data=TriggerPagCallback(pk=trigger.pk))
    builder.adjust(2)
    next_page = InlineKeyboardButton(text="▶", callback_data=TriggerPagenCallback(st=start + 6, stop=stop + 6).pack())
    previous_page = InlineKeyboardButton(text="◀",
                                         callback_data=TriggerPagenCallback(st=start - 6, stop=stop - 6).pack())
    if len(triggers) > 6:
        builder.row(previous_page, next_page)
    back = InlineKeyboardButton(text='🔙 Назад', callback_data='wait_answer')
    builder.row(back)
    return builder.as_markup()
