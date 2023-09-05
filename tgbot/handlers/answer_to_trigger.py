import re

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hlink, hcode
from loguru import logger

from tgbot.keyboards.callback_data import TriggerCallback
from tgbot.keyboards.triggers_kb import trigger_kb
from tgbot.misc.api_wb_methods import ApiClient
from tgbot.models.db_commands import get_answer_trigger

trigger_router = Router()


@trigger_router.callback_query(TriggerCallback.filter())
async def send_answer_tr(call: CallbackQuery, callback_data: TriggerCallback):
    trigger = await get_answer_trigger(callback_data.id)
    await ApiClient.send_feedback(trigger.market.token, trigger.feedback_id, trigger.answer)
    trigger.answered_feed = True
    trigger.save()
    logger.info(f'Пользователь {trigger.market.user.username} ID: {trigger.market.user.telegram_id} ОТВЕТИЛ НА ТРИГГЕР')
    await call.message.edit_text(text=call.message.text + '\n\n✅ Отзыв опубликован! ✅')


@trigger_router.callback_query(F.data == 'del_kb')
async def del_kb_trigger(call: CallbackQuery):
    await call.message.delete_reply_markup()


@trigger_router.message(F.text.contains('@wb_auto_comment_bot tr'))
async def regexp_func(message: Message):
    pattern = r'@wb_auto_comment_bot tr Не удаляйте эту строку \(редактируйте только текст отзыва\)' \
              r' feedback_id=(.{20})\n\n(.*)'
    matches = re.findall(pattern, message.text, re.DOTALL)
    if not matches:
        return await message.answer("Ошибка при изменение отзыва триггера 🆘")
    feedback_id = matches[0][0]
    check_trigger_id = await get_answer_trigger(feedback_id)
    if not check_trigger_id:
        return await message.answer("Ошибка при изменение отзыва триггера 🆘")
    remaining_text = matches[0][1].strip()
    check_trigger_id.answer = remaining_text
    check_trigger_id.save()
    text_for_edit = f"tr Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={check_trigger_id.feedback_id}\n\n" \
                    f"{remaining_text}"
    text = '\n'.join([f'Количество звезд: {check_trigger_id.rating} ⭐\n',
                      f'{hbold("Товар")}: {hlink(check_trigger_id.name_item, check_trigger_id.link_item)}',
                      f'{hbold("Текст отзыва")}:\n{hcode(check_trigger_id.text)}\n',
                      ])

    result_text = "\n".join([f'Отзыв изменен ✅\n', f'{hbold("Магазин")}: {check_trigger_id.market.name_market}', text,
                             f"{hbold('Отредактированный ответ')}:\n{remaining_text}"])
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await message.answer(text=result_text,
                         reply_markup=await trigger_kb(check_trigger_id.feedback_id, text_for_edit))
