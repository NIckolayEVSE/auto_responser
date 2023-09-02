from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from loguru import logger

from tgbot.config import Config
from tgbot.keyboards.callback_data import ManualCallback
from tgbot.keyboards.inline import main_menu_kb, gen_again_kb, back_to_main_menu, back_menu_bot_kb, first_show_bot_kb
from tgbot.misc.main_texts_and_funcs import generate_text_func
from tgbot.misc.states import EnterYourItemState
from tgbot.models.db_commands import create_client, select_client, create_manual_feed, select_manual_feed

user_router = Router()


@user_router.message(Command(commands=["start"]))
async def user_start(message: Message, state: FSMContext):
    """
    Показывает главное меню при нажатии команды /start
    """
    user = await select_client(message.from_user.id)
    await state.clear()
    if not user:
        await create_client(telegram_id=message.from_user.id, username=message.from_user.username,
                            name=message.from_user.full_name, url=message.from_user.url)
        logger.info("Создан пользователь ID: {} USERNAME: {}".format(message.from_user.id, message.from_user.username))
        # return await message.answer_audio(
        #     audio='BAACAgIAAxkBAAIC1GS36EiKh67fXRwgRm7FRyn4VAX3AALbMgACM9LBSTCRON3AUg02LwQ',
        #     caption='Пожалуйста, прежде чем, начать пользоваться ботом'
        #             ' ознакомьтесь с инструкцией 📖', reply_markup=await first_show_bot_kb())

    await message.answer(text="Главное меню 🧾", reply_markup=await main_menu_kb())


@user_router.callback_query(F.data == 'back_to_menu')
async def back_to_menu_from_mw(call: CallbackQuery, state: FSMContext):
    """
    Срабатывает после команды "Оформил" в middleware
    """
    await state.clear()
    try:
        await call.message.edit_text(text="Главное меню 🧾", reply_markup=await main_menu_kb())
    except TelegramBadRequest:
        await call.message.delete_reply_markup()
        await call.message.answer(text="Главное меню 🧾", reply_markup=await main_menu_kb())


@user_router.callback_query(F.data == 'instruction')
async def instruction(call: CallbackQuery):
    text = 'Для правильного использования бота вы можете посмотреть видео-инструкцию 🎞'
    await call.message.answer_audio(audio='BAACAgIAAxkBAAIC1GS36EiKh67fXRwgRm7FRyn4VAX3AALbMgACM9LBSTCRON3AUg02LwQ',
                                    caption=text, reply_markup=await back_menu_bot_kb())


@user_router.callback_query(F.data == 'create_anw')
async def create_answer_func(call: CallbackQuery, state: FSMContext):
    text = f'{hbold("Введите название товара и текст отзыва в поле ввода. Я сгенерирую ответ")}\n\n' \
           f'Пример:\n{hcode("Слитный купальник. Хороший купальник! Ткань очень хорошая, на теле сидит идеально. Размер подошёл.")}'
    await call.message.edit_text(text=text, reply_markup=await back_to_main_menu())
    await state.set_state(EnterYourItemState.item_feedback_state)


@user_router.message(EnterYourItemState.item_feedback_state, F.text)
async def enter_item_feedback_state(message: Message, state: FSMContext, bot: Bot, config: Config):
    text_feedback = message.text
    user = await select_client(message.from_user.id)
    feed_id = await create_manual_feed(user, text_feedback)
    message_delete = await message.answer('Генерирую ответ, пожалуйста, подождите ⏱')
    answer_text = await generate_text_func(text_feedback, bot, config)
    await message_delete.delete()
    text_result = f'{hbold("Ваш отзыв")}:\n\n{hcode(text_feedback)}\n\n{hbold("Сгенерированный ответ:")}\n\n{hcode(answer_text)}'
    await message.answer(text=text_result, reply_markup=await gen_again_kb(feed_id))
    await state.set_state(None)


@user_router.callback_query(ManualCallback.filter())
async def gen_again_func(call: CallbackQuery, bot: Bot, callback_data: ManualCallback, config: Config):
    feed = await select_manual_feed(callback_data.id)
    answer_text = await generate_text_func(feed.feedback, bot, config)
    text_result = f'{hbold("Ваш отзыв")}:\n\n{hcode(feed.feedback)}\n\n{hbold("Сгенерированный новый ответ:")}\n\n{answer_text}'
    await call.message.edit_text(text=text_result, reply_markup=await gen_again_kb(feed))
