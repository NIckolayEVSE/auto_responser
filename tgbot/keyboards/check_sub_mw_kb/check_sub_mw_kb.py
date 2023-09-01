from aiogram.utils.keyboard import InlineKeyboardBuilder


async def subscribe_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Оформить подписку", url="https://t.me/testingbotchannells")
    keyboard.button(text="Оформил", callback_data="back_to_menu")
    return keyboard.adjust(1).as_markup()
