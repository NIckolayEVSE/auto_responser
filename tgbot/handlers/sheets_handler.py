import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from tgbot.config import Config
from tgbot.keyboards.callback_data import EditModeGenerate, EditMode, MarketsTables
from tgbot.keyboards.sheets_kb import add_market_kb, menu_sheet_kb, edit_sheet_mode_kb, markets_all_kb, cancel_add_url, \
    markets_url
from tgbot.misc.main_texts_and_funcs import mode_edit_text, validate_email, create_table
from tgbot.misc.states import AddGmailState
from tgbot.models.db_commands import select_client, select_market, create_gmail, select_markets

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
async def edit_mode(call: CallbackQuery, callback_data: EditModeGenerate):
    market = await select_market(pk=callback_data.id)
    await call.message.edit_text(text=mode_edit_text(market), reply_markup=await edit_sheet_mode_kb(market))


@sheets_router.callback_query(EditMode.filter())
async def edit_mode_sheet(call: CallbackQuery, callback_data: EditMode):
    market = await select_market(callback_data.id)
    if callback_data.mode == 'use_sheet':
        market.use_sheet = True
    elif callback_data.mode == 'not_use_sheet':
        market.use_sheet = False
    market.save()
    await call.message.edit_text(text=mode_edit_text(market),
                                 reply_markup=await edit_sheet_mode_kb(market))


@sheets_router.callback_query(F.data == 'add_sheet')
async def add_sheet(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await select_client(call.message.chat.id)
    markets = user.wb_token.filter(use_sheet=True)
    text = 'Выберите магазин к которому хотите добавить таблицу'
    if not markets:
        text = 'У вас пока нет таблиц  ❌'
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
    text = 'Выберите магазин, чтобы прейти по ссылке на таблицу'
    if not markets:
        text = 'У вас пока нет таблиц  ❌'
    await call.message.edit_text(text, reply_markup=await markets_url(markets))
