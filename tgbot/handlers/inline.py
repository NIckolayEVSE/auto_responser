import re

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.markdown import hcode, hlink, hbold

from tgbot.config import Config
from tgbot.keyboards.callback_data import AnswerFeedback, AnswerPhotoFeedback, NewGen
from tgbot.keyboards.on_check_feed_kb import on_check_kb
from tgbot.misc.api_wb_methods import ApiClient
from tgbot.misc.main_texts_and_funcs import generate_text_func, send_error
from tgbot.models.db_commands import select_feedback

inline_router = Router()


@inline_router.message(F.text)
async def regexp_func(message: Message):
    pattern = r'@wb_auto_comment_bot Не удаляйте эту строку \(редактируйте только текст отзыва\) feedback_id=(.{20})\n\n(.*)'
    matches = re.findall(pattern, message.text, re.DOTALL)
    if not matches:
        return await message.answer("Ошибка при изменение отзыва 🆘")
    feedback_id = matches[0][0]
    check_feedback_id = await select_feedback(feedback_id)
    if not check_feedback_id:
        return await message.answer("Ошибка при изменение отзыва 🆘")
    remaining_text = matches[0][1].strip()
    feedback = await select_feedback(feedback_id)
    feedback.answer = remaining_text
    feedback.save()
    text_for_edit = f"Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={feedback.feedback_id}\n\n" \
                    f"{remaining_text}"
    text = '\n'.join([f'Количество звезд: {feedback.rating} ⭐\n',
                      f'{hbold("Товар")}: {hlink(feedback.name_item, feedback.link_feedback)}',
                      f'{hbold("Текст отзыва")}\n{hcode(feedback.feedback)}\n',
                      ])

    result_text = "\n".join([f'Отзыв изменен ✅\n', f'{hbold("Магазин")}: {feedback.market.name_market}', text,
                             f"{hbold('Отредактированный ответ')}:\n{remaining_text}"])
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await message.answer(text=result_text,
                         reply_markup=await on_check_kb(feedback.feedback_id, text_for_edit, feedback.link_photos))


@inline_router.callback_query(AnswerFeedback.filter())
async def send_answer(call: CallbackQuery, callback_data: AnswerFeedback, bot: Bot, config: Config):
    feedback = await select_feedback(callback_data.id)
    feedback.answered_feed = True
    try:
        await ApiClient.send_feedback(feedback.market.token, feedback.feedback_id, feedback.answer)
        feedback.save()
    except Exception as error:
        await call.message.answer('При отправке отзыва произошла ошибка!')
        text = f'При отправке отзыва ID {callback_data.id} произошла ошибка: {error}'
        return await send_error(bot, config, error_text=text)
    await call.message.delete_reply_markup()
    await call.message.answer("Отзыв опубликован! ✅")


@inline_router.callback_query(AnswerPhotoFeedback.filter())
async def send_photo(call: CallbackQuery, callback_data: AnswerPhotoFeedback):
    feedback = await select_feedback(callback_data.id)
    link_photos = feedback.link_photos.split(',') if feedback.link_photos else ''
    if not link_photos:
        return await call.answer('У этого товара нет фото ❎')
    media = [InputMediaPhoto(media=i) for i in link_photos]  # i: str
    await call.message.answer_media_group(media)


@inline_router.callback_query(F.data == 'do_not_answer')
async def do_not_answer(call: CallbackQuery):
    await call.message.delete_reply_markup()


@inline_router.callback_query(NewGen.filter())
async def new_gen(call: CallbackQuery, callback_data: NewGen, bot: Bot, config: Config):
    message_del = await call.message.answer('Подождите идет генерация ⏱')
    feedback = await select_feedback(callback_data.id)
    answer = await generate_text_func(feedback.feedback, bot, config)
    feedback.answer = answer
    feedback.save()
    await message_del.delete()
    text_for_edit = f"Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={feedback.feedback_id}\n\n" \
                    f"{answer}"
    text = f'{hbold("Оценка")}: {feedback.rating} ⭐\n' \
           f'{hbold("Товар")}: {hlink(feedback.name_item, feedback.link_feedback)}' \
           f'{hbold("Текст отзыва")}\n{hcode(feedback.feedback)}\n'
    result_text = "\n".join([f'Новый отзыв сгенерирован ✅\n',
                             f'{hbold("Магазин")}: {feedback.market.name_market}',
                             text,
                             f"{hbold('Новый ответ')} 🆕:\n{answer}"])
    await call.message.edit_text(text=result_text, reply_markup=await on_check_kb(feedback.feedback_id, text_for_edit,
                                                                                  feedback.link_photos))
