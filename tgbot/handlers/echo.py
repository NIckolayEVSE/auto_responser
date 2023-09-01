from aiogram import types, Router, F

echo_router = Router()


@echo_router.message(F.text)
async def bot_echo(message: types.Message):
    if not message.text.startswith('@wb_auto_comment_bot'):
        await message.answer("Такой команды не существует")
