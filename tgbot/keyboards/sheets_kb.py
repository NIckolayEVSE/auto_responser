from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import EditMode, MarketsTables


async def add_market_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Подключить магазин', callback_data='my_cabinets')
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def menu_sheet_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🗂 Мои таблицы', callback_data='my_sheets')
    kb.button(text='➕ Добавить таблицу', callback_data='add_sheet')
    kb.button(text='📘 Инструкция', callback_data='instruct_sheet')
    kb.button(text='🔙 Назад', callback_data='my_office')
    return kb.adjust(1).as_markup()


async def edit_sheet_mode_kb(market):
    kb = InlineKeyboardBuilder()
    if not market.use_sheet:
        kb.button(text='Исп. таблицы', callback_data=EditMode(id=market.pk, mode='use_sheet'))
    else:
        kb.button(text='Исп. GPT', callback_data=EditMode(id=market.pk, mode='not_use_sheet'))
    kb.button(text='🔙 Назад', callback_data='table_sheet')
    return kb.adjust(1).as_markup()


async def markets_all_kb(markets):
    kb = InlineKeyboardBuilder()
    for market in markets:
        if market.use_sheet and market.gmail_markets.first():
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
