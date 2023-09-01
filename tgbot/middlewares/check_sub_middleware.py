from typing import Callable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hlink
from typing_extensions import Awaitable

from tgbot.keyboards.check_sub_mw_kb.check_sub_mw_kb import subscribe_kb
from tgbot.models.db_commands import select_client


class CheckSubscribeMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, CallbackQuery):
            user = await select_client(event.message.chat.id)
            chat_id = event.message.chat.id
        else:
            user = await select_client(event.chat.id)
            chat_id = event.chat.id
        if not user:
            return await handler(event, data)
        subscribe = await data['bot'].get_chat_member(chat_id='@testingbotchannells', user_id=chat_id)
        if subscribe.status in ('creator', 'administrator', 'member'):
            return await handler(event, data)
        else:
            text = [
                f'{hbold("Для пользования бота нужно оформить подписку в ")}'
                f' {hlink("боте", "https://t.me/testingbotchannells")}\n'
            ]
            if isinstance(event, CallbackQuery):
                await event.message.answer(text='\n'.join(text), reply_markup=await subscribe_kb(),
                                           disable_web_page_preview=True)
            else:
                await event.answer(text='\n'.join(text), reply_markup=await subscribe_kb(),
                                   disable_web_page_preview=True)
