from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import TriggerCallback


async def trigger_kb(tigger, text):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🌐 Опубликовать', callback_data=TriggerCallback(id=tigger.pk))
    keyboard.button(text='📝 Редактировать отзыв', switch_inline_query_current_chat=text)
    keyboard.button(text='❌ Не отвечать на отзыв', callback_data='del_kb')
    return keyboard.adjust(1).as_markup()
