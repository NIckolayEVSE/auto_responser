import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hlink, hcode

from tgbot.config import Config
from tgbot.keyboards.callback_data import EditModeGenerate, EditMode, MarketsTables, TriggerPagenCallback, \
    TriggerPagCallback, AnswerSheetPagen, AnswerSheet
from tgbot.keyboards.on_check_feed_kb import on_check_kb
from tgbot.keyboards.sheets_kb import add_market_kb, menu_sheet_kb, edit_sheet_mode_kb, markets_all_kb, cancel_add_url, \
    markets_url, type_feeds_kb, pagen_triggers, back_triggers, pagen_answers_sheet
from tgbot.keyboards.triggers_kb import trigger_kb
from tgbot.misc.main_texts_and_funcs import mode_edit_text, validate_email, create_table
from tgbot.misc.states import AddGmailState
from tgbot.models.db_commands import select_client, select_market, create_gmail, select_markets, select_all_triggers, \
    get_answer_trigger, select_feedback_sheet, select_feedback, select_feedback_pk, get_answer_trigger_pk

sheets_router = Router()


@sheets_router.callback_query(F.data == 'table_sheet')
async def table_sheet(event: CallbackQuery | Message, state: FSMContext):
    await state.clear()
    if isinstance(event, CallbackQuery):
        user = await select_client(event.message.chat.id)
    else:
        user = await select_client(event.chat.id)
    markets = user.wb_token.all().count()
    if not markets:
        text = "\n".join([
            'Кажется у вас нет магазинов.🚫',
            'Для использования табличной генерации подключите магазин'
        ])
        return await event.message.edit_text(text=text, reply_markup=await add_market_kb())
    if isinstance(event, CallbackQuery):
        await event.message.edit_text('Меню табличной генерации', reply_markup=await menu_sheet_kb())
    else:
        await event.answer('Меню табличной генерации', reply_markup=await menu_sheet_kb())


@sheets_router.callback_query(EditModeGenerate.filter())
async def edit_mode(call: CallbackQuery, callback_data: EditModeGenerate, state: FSMContext):
    market = await select_market(pk=callback_data.id)
    await state.update_data(id_empty_market=callback_data.id)
    await call.message.edit_text(text=mode_edit_text(market), reply_markup=await edit_sheet_mode_kb(market))


@sheets_router.callback_query(EditMode.filter())
async def edit_mode_sheet(call: CallbackQuery, callback_data: EditMode, state: FSMContext):
    market = await select_market(callback_data.id)
    if callback_data.mode == 'use_sheet':
        market.use_sheet = True
    elif callback_data.mode == 'not_use_sheet':
        market.use_sheet = False
    market.save()
    await state.update_data(id_empty_market=callback_data.id)
    await call.message.edit_text(text=mode_edit_text(market),
                                 reply_markup=await edit_sheet_mode_kb(market))


@sheets_router.callback_query(F.data == 'add_sheet')
async def add_sheet(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await select_client(call.message.chat.id)
    markets = user.wb_token.filter(use_sheet=True)
    text = 'Выберите магазин к которому хотите добавить таблицу'
    if not markets:
        text = 'У вас пока нет магазинов, которым можно добавить талицу ❗'
    await call.message.edit_text(text, reply_markup=await markets_all_kb(markets))


@sheets_router.callback_query(MarketsTables.filter())
async def create_sheet(call: CallbackQuery, callback_data: MarketsTables, state: FSMContext):
    text = "\n".join([f'Для использования таблиц введите вашу {hbold("gmail")} почту',
                      f'Обращаем ваше внимание, что почта может быть только {hbold("gmail")}',
                      f'Пример: {hbold("example@gmail.com")}'])
    await state.update_data(market_pk=callback_data.id)
    await call.message.edit_text(text, reply_markup=await cancel_add_url('🔙 Назад'))
    await state.set_state(AddGmailState.gmail)


@sheets_router.message(AddGmailState.gmail)
async def add_gmail(message: Message, state: FSMContext, config: Config):
    if not validate_email(message.text):
        text = "\n".join([f'Кажется вы ввели не верную почту 🚫',
                          f'Попробуйте еще раз или нажмите на кнопку {hbold("Отмена")}',
                          f'Почта должна быть формата {hbold("example@gmail.com")}'])
        return await message.answer(text, reply_markup=await cancel_add_url('❌ Отмена'))
    data = await state.get_data()
    market = await select_market(data.get("market_pk"))
    message_edit = await message.answer('Подождите, идет создание таблицы 🕘')

    cfg = config.misc.google_table
    name = f'Автоответчик Магазин: {market.name_market}'

    # loop = asyncio.get_running_loop()
    # with ProcessPoolExecutor() as pool:
    #     url = await loop.run_in_executor(pool, create_table, message.text, name, cfg)

    executor = ThreadPoolExecutor(max_workers=3)
    future = executor.submit(create_table, message.text, name, cfg)
    url = future.result()

    await create_gmail(market, url)

    await message_edit.edit_text(text='Заполняю данные ...')
    await message_edit.delete()
    text_gmail = "\n".join(['Таблица успешно создана! 😎',
                            f'Ссылка на талицу для магазина {market.name_market}',
                            f'{url}'])
    await message.answer(text_gmail)
    await asyncio.sleep(1)
    await table_sheet(message, state)


@sheets_router.callback_query(F.data == 'my_sheets')
async def my_sheets(call: CallbackQuery):
    user = await select_client(call.message.chat.id)
    markets = await select_markets(user)
    text = 'Выберите магазин, чтобы перейти по ссылке на таблицу'
    if not markets:
        text = 'У вас пока нет таблиц  ❌'
    await call.message.edit_text(text, reply_markup=await markets_url(markets))


@sheets_router.callback_query(F.data == 'wait_answer')
async def wait_answer(call: CallbackQuery):
    text = 'В данном меню вы можете просмотреть неотвеченные отзывы, сгенерированные с использованием {}\n\n' \
           'Выберите категорию отзывов'.format(hbold("таблиц"))
    await call.message.edit_text(text, reply_markup=await type_feeds_kb())


@sheets_router.callback_query(F.data == 'cat_trig')
async def category_triggers(call: CallbackQuery):
    triggers = await select_all_triggers(await select_client(call.message.chat.id))
    if not triggers:
        return await call.message.edit_text('У вас нет неотвеченных отзывов с триггерами',
                                            reply_markup=await back_triggers())
    await call.message.edit_text('Выберите неотвеченный отзыв с триггером',
                                 reply_markup=await pagen_triggers(triggers, 0, 6))


@sheets_router.callback_query(TriggerPagenCallback.filter())
async def pagination_triggers(call: CallbackQuery, callback_data: TriggerPagenCallback):
    triggers = await select_all_triggers(await select_client(call.message.chat.id))
    try:
        await call.message.edit_text('Выберите неотвеченный отзыв с триггером',
                                     reply_markup=await pagen_triggers(triggers, callback_data.st, callback_data.stop))
    except TelegramBadRequest as _err:
        # print(_err)
        await call.answer()


@sheets_router.callback_query(TriggerPagCallback.filter())
async def details_trigger(call: CallbackQuery, callback_data: TriggerPagCallback):
    trigger = await get_answer_trigger_pk(callback_data.pk)
    text = '\n'.join([f'Ответ с {hbold("Триггером")}',
                      f'{trigger.trigger}\n',
                      f'{hbold("Оценка")}: {trigger.rating} ⭐\n',
                      f'{hbold("Товар")}: {hlink(trigger.name_item, trigger.link_item)}',
                      f'{hbold("Текст отзыва")}\n{hcode(trigger.text)}',
                      f'{hbold("Ссылка на отзыв")}: {trigger.link_feed}\n',
                      f"\n{hbold('Предварительный ответ')}:\n{trigger.answer}"
                      ])
    text_for_edit = "\n".join(
        [f"tr Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={trigger.feedback_id}\n",
         f'{trigger.answer}']
    )
    await call.message.edit_text(text=text, reply_markup=await trigger_kb(trigger, text_for_edit, 'back'))


@sheets_router.callback_query(F.data == 'no_trig')
async def feedback_without_triggers(call: CallbackQuery):
    answers = await select_feedback_sheet(await select_client(call.message.chat.id))
    if not answers:
        return await call.message.edit_text('У вас нет неотвеченных отзывов без триггеров',
                                            reply_markup=await back_triggers())
    await call.message.edit_text('Выберите неотвеченный отзыв с триггером',
                                 reply_markup=await pagen_answers_sheet(answers, 0, 6))


@sheets_router.callback_query(AnswerSheetPagen.filter())
async def pagination_triggers(call: CallbackQuery, callback_data: AnswerSheetPagen):
    answers = await select_feedback_sheet(await select_client(call.message.chat.id), callback_data.generate)
    back_call = 'my_office' if callback_data.generate else 'wait_answer'
    mode = bool(callback_data.generate)
    text = 'Выберите неотвеченный отзыв'
    if callback_data.generate:
        text = "\n".join([
            f'В данном меню вы можете просмотреть неотвеченные отзывы, сгенерированные с использованием {hbold("GPT генерации")}\n',
            text
        ])
    try:
        await call.message.edit_text(text, reply_markup=await pagen_answers_sheet(answers, callback_data.st,
                                                                                  callback_data.stop,
                                                                                  back_call=back_call,
                                                                                  mode=mode))
    except TelegramBadRequest as _err:
        # print(_err)
        await call.answer()


@sheets_router.callback_query(AnswerSheet.filter())
async def details_trigger(call: CallbackQuery, callback_data: AnswerSheet, state: FSMContext):
    answer = await select_feedback_pk(callback_data.pk)
    text = "\n".join([f'Отзыв\n', f'{hbold("Магазин")}: {answer.market.name_market}\n',
                      f'{hbold("Оценка")}: {answer.rating} ⭐',
                      f'{hbold("Товар")}: {hlink(answer.name_item, answer.link_feedback)}\n',
                      f'{hbold("Текст отзыва")}:',
                      f'{hcode(answer.feedback) if answer.feedback else hbold("У этого отзыва только оценка")}\n',
                      f'{hbold("Ответ")}:', f'{answer.answer}'
                      ])

    text_for_edit = "\n".join([
        f"Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={answer.feedback_id}\n",
        f"{answer.answer}"
    ])
    gen = 'gen' if callback_data.generate else 'not_gen'
    back = 'wait_answer_gpt' if callback_data.generate else 'no_trig'
    await state.update_data(gen=gen, back=back)
    await call.message.edit_text(text=text, reply_markup=await on_check_kb(answer.feedback_id, text_for_edit,
                                                                           answer.link_photos, gen, back))
