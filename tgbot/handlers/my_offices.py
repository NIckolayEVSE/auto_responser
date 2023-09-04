import asyncio

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from tgbot.config import Config
from tgbot.keyboards.callback_data import FirstMarket, EditModeMessages, DeleteMarket, EmptyTextCallback, \
    EditEmptyTextCallback
from tgbot.keyboards.inline import myself_office_kb, add_office_kb, cancel_add_token, check_setting_market, \
    adit_mode_messages, delete_market_kb, answer_to_empty_kb
from tgbot.misc.api_wb_methods import ApiClient
from tgbot.misc.main_texts_and_funcs import set_market_autosend_state, set_market_stars, validate_list_stars, \
    empty_text, send_error
from tgbot.misc.states import EnterTokenState, EditStarsList
from tgbot.models.db_commands import select_client, create_name_market_wb, select_market, select_token

my_office_router = Router()


@my_office_router.callback_query(F.data == 'my_office')
async def my_office_func(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text='Личный кабинет 👨🏼‍💻', reply_markup=await myself_office_kb())


@my_office_router.callback_query(F.data == 'my_cabinets')
async def my_cabinets_func(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await select_client(call.message.chat.id)
    cabinets = user.wb_token.all()
    text = 'Список ваших магазинов: 🏬\n\nПоддерживается добавление до 5 магазинов включительно\n' \
           f'Сейчас добавлено магазинов: {cabinets.count() if cabinets.count() else 0}'
    if not cabinets:
        text = 'У вас пока нет магазинов!  🈴'
    await call.message.edit_text(text, reply_markup=await add_office_kb(cabinets))


@my_office_router.callback_query(F.data == 'add_token')
async def add_token_func(call: CallbackQuery, state: FSMContext):
    text = "\n".join([f'Укажите {hbold("Стандартный")} токен.🔑\n\n{hbold("Как получить токен: 🗝")}',
                      f'1. Перейдите в личный кабинет WB ⏩ Профиль ⏩ Настройки ⏩ Доступ к API',
                      f'Или перейдите по ссылке: https://seller.wildberries.ru/supplier-settings/access-to-api',
                      f'2. Нажмите кнопку ▶"{hbold("Создать новый токен")}"',
                      f'3. Выберите тип токена {hbold("Стандартный 🗝")}, введите название магазина Ⓜ и нажмите кнопку ▶{hbold("Создать токен")}\n',
                      f'Созданный токен 🔑 вставьте ниже 👇'])
    await call.message.edit_text(text, reply_markup=await cancel_add_token(),
                                 disable_web_page_preview=False)
    await state.set_state(EnterTokenState.enter_token)


@my_office_router.message(EnterTokenState.enter_token, F.text)
async def enter_token_func(message: Message, state: FSMContext, config: Config, bot: Bot):
    token = message.text
    token_already_registered_msg = 'Похоже этот токен уже зарегистрирован 🆘\n\n' + \
                                   'Попробуйте еще раз 🔄 или нажмите кнопку <b>Отмена</b> ❌'

    incorrect_token_msg = 'Похоже вы ввели не верный токен 🔑\n\n' + \
                          'Попробуйте еще раз 🔄 или нажмите кнопку <b>Отмена</b> ❌'

    prompt_market_name_msg = 'Придумайте имя вашего магазина 👇'

    in_db_token, status_token = await asyncio.gather(
        select_token(token),
        ApiClient(api_key=token).check_standard_token()
    )
    if in_db_token:
        return await message.answer(text=token_already_registered_msg, reply_markup=await cancel_add_token())
    if status_token != 200:
        user = await select_client(message.from_user.id)
        tokens = user.inc_wb_token.all().count()
        text = "\n".join([
            f'Новый пользователь у которого не верный токен USERNAME: {user.username} ID: {user.telegram_id}\n',
            'Всего не верных токенов {}'.format(tokens)
        ])
        await send_error(bot, config, error_text=text)
        return await message.answer(text=incorrect_token_msg, reply_markup=await cancel_add_token())

    await state.update_data(token=token)
    await message.answer(prompt_market_name_msg, reply_markup=await cancel_add_token())
    await state.set_state(EnterTokenState.enter_market_name)


@my_office_router.message(EnterTokenState.enter_market_name, F.text)
async def enter_market_name_func(message: Message, state: FSMContext):
    name_market = message.text
    user = await select_client(message.from_user.id)
    data = await state.get_data()
    market_pk = await create_name_market_wb(user=user, token=data.get('token'), name_market=name_market)
    await message.answer(text=f'Вы создали магазин:\n\n<b>{name_market}</b> 🏪',
                         reply_markup=await check_setting_market(market_pk))
    await state.clear()


@my_office_router.callback_query(FirstMarket.filter())
async def check_first_market_func(event: CallbackQuery | Message, callback_data: FirstMarket, state: FSMContext):
    market = await select_market(callback_data.id)
    text = "\n".join([f'Настройка магазина:\n\n<b>{market.name_market}</b>\n',
                      'Здесь вы можете гибко настроить, как бот будет отвечать на ваши отзывы,'
                      ' в зависимости от их оценки.\n',
                      'Например:',
                      'Вы можете выбрать, чтобы на отзывы с оценкой 5 и 4 звезды бот отвечал в'
                      ' полностью автоматическом режиме. На все остальные отзывы [с оценками 3, 2, 1 звезда] бот'
                      ' будет создавать ответ, но будет присылать вам на согласование.\n',
                      'Ваш текущий режим ответов:\n',
                      f'1. ⭐️ - {"Автоматический" if market.auto_send_star_1 else "Полуавтоматический"}',
                      f'2. ⭐️⭐️ - {"Автоматический" if market.auto_send_star_2 else "Полуавтоматический"}',
                      f'3. ⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_3 else "Полуавтоматический"}',
                      f'4. ⭐️⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_4 else "Полуавтоматический"}',
                      f'5. ⭐️⭐️⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_5 else "Полуавтоматический"}\n',
                      f'Если хотите изменить режим для одной или нескольких оценок — введите их через запятую. '
                      f'Например: 1, 2, 3'])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=await adit_mode_messages(market))
    else:
        await event.answer(text=text, reply_markup=await adit_mode_messages(market))
    await state.update_data(pk=callback_data.id)
    await state.set_state(EditStarsList.enter_list_stars)


@my_office_router.message(EditStarsList.enter_list_stars, F.text)
async def enter_list_stars_func(message: Message, state: FSMContext):
    list_stars = message.text.replace(' ', '')
    data = await state.get_data()
    market = await select_market(int(data['pk']))

    if not validate_list_stars(list_stars):
        await message.answer("Кажется вы ошиблись с вводом! 🆘\n\nПопробуйте еще раз 🔄")
        return await check_first_market_func(message, FirstMarket(id=int(data['pk'])), state=state)

    for star in list_stars.split(','):
        set_market_stars(market, int(star))

    market.save()
    await check_first_market_func(message, FirstMarket(id=int(data['pk'])), state=state)


@my_office_router.callback_query(EditModeMessages.filter())
async def choose_mode_messages(call: CallbackQuery, callback_data: EditModeMessages, state: FSMContext):
    await state.clear()
    market = await select_market(callback_data.id)
    text = ''
    if callback_data.mode_mes == 'auto':
        set_market_autosend_state(market, True)
        text = 'Вы изменили режим отправки сообщений на Автоматический 🤖'
    elif callback_data.mode_mes == 'not_auto':
        set_market_autosend_state(market, False)
        text = 'Вы изменили режим отправки сообщений на Полуавтоматический 📺'
    market.save()
    await call.answer(text=text, show_alert=True)
    await check_first_market_func(call, FirstMarket(id=callback_data.id), state=state)


@my_office_router.callback_query(DeleteMarket.filter())
async def delete_func(call: CallbackQuery, callback_data: DeleteMarket, state: FSMContext):
    market = await select_market(callback_data.id)
    await call.message.edit_text(f'Вы точно хотите удалить магазин <b>{market.name_market}</b>? 📛',
                                 reply_markup=await delete_market_kb())
    await state.update_data(pk_del=callback_data.id)


@my_office_router.callback_query(F.data == 'yes_del')
async def delete_market(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    market = await select_market(data.get('pk_del'))
    market.delete()
    await call.answer('Вы успешно удалили магазин ✅ -> 🗑')
    await my_cabinets_func(call, state)


@my_office_router.callback_query(EmptyTextCallback.filter())
async def set_empty_text(call: CallbackQuery, callback_data: EmptyTextCallback, state: FSMContext):
    market = await select_market(callback_data.id)
    await state.update_data(id_empty_market=callback_data.id)
    await call.message.edit_text(text=empty_text(market.send_empty_text),
                                 reply_markup=await answer_to_empty_kb(market))


@my_office_router.callback_query(EditEmptyTextCallback.filter())
async def choose_mode_empty_text(call: CallbackQuery, callback_data: EditEmptyTextCallback, state: FSMContext):
    market = await select_market(callback_data.id)
    if callback_data.mode == 'stop_answer':
        market.send_empty_text = False
    elif callback_data.mode == 'ok_answer':
        market.send_empty_text = True
    market.save()
    await state.update_data(id_empty_market=callback_data.id)
    await call.message.edit_text(text=empty_text(market.send_empty_text),
                                 reply_markup=await answer_to_empty_kb(market))


@my_office_router.callback_query(F.data == 'back_to_call')
async def back_to_call(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await check_first_market_func(call, FirstMarket(id=data.get('id_empty_market')), state=state)
