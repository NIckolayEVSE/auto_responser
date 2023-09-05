from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import EditMode, MarketsTables, TriggerPagCallback, TriggerPagenCallback, \
    AnswerSheet, AnswerSheetPagen


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
    kb.button(text='Триггеры', callback_data='cat_trig')
    kb.button(text='Без триггеров', callback_data='no_trig')
    kb.button(text='🔙 Назад', callback_data='table_sheet')
    return kb.adjust(1).as_markup()


## дата, название
async def pagen_triggers(triggers, start: int, stop: int):
    kb = InlineKeyboardBuilder()
    if start < 0:
        start = 0
        stop = 6
    elif start > len(triggers) - 1:
        start = 0
        stop = 6
    for trigger in triggers[start:stop]:
        answer = trigger.created.strftime('%H:%M') + " " + trigger.created.strftime('%d.%m.%Y') + ' ' + trigger.trigger
        kb.button(text=answer, callback_data=TriggerPagCallback(pk=trigger.pk))
    kb.adjust(2)
    next_page = InlineKeyboardButton(text="▶", callback_data=TriggerPagenCallback(st=start + 6, stop=stop + 6).pack())
    previous_page = InlineKeyboardButton(text="◀",
                                         callback_data=TriggerPagenCallback(st=start - 6, stop=stop - 6).pack())
    if len(triggers) > 6:
        kb.row(previous_page, next_page)
    back = InlineKeyboardButton(text='🔙 Назад', callback_data='wait_answer')
    kb.row(back)
    return kb.as_markup()


async def back_triggers():
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='wait_answer')
    return kb.as_markup()


async def pagen_answers_sheet(answers, start: int, stop: int):
    kb = InlineKeyboardBuilder()
    if start < 0:
        start = 0
        stop = 6
    elif start > len(answers) - 1:
        start = 0
        stop = 6
    for answer in answers[start:stop]:
        answer = answer.created_at.strftime('%H:%M') + " " + answer.created_at.strftime(
            '%d.%m.%Y') + ' ' + answer.answer[:20]
        kb.button(text=answer, callback_data=AnswerSheet(pk=answer.pk))
    kb.adjust(2)
    next_page = InlineKeyboardButton(text="▶", callback_data=AnswerSheetPagen(st=start + 6, stop=stop + 6).pack())
    previous_page = InlineKeyboardButton(text="◀",
                                         callback_data=AnswerSheetPagen(st=start - 6, stop=stop - 6).pack())
    if len(answers) > 6:
        kb.row(previous_page, next_page)
    back = InlineKeyboardButton(text='🔙 Назад', callback_data='wait_answer')
    kb.row(back)
    return kb.as_markup()
