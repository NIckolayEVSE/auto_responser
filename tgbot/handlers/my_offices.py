from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from tgbot.keyboards.callback_data import FirstMarket, EditModeMessages, DeleteMarket
from tgbot.keyboards.inline import myself_office_kb, add_office_kb, cancel_add_token, check_setting_market, \
    adit_mode_messages, delete_market_kb
from tgbot.misc.api_wb_methods import ApiClient
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
           f'Сейчас добавлено магазинов: {cabinets.count()}'
    if not cabinets:
        text = 'У вас пока нет магазинов! 🈴'
    await call.message.edit_text(text, reply_markup=await add_office_kb(cabinets))


@my_office_router.callback_query(F.data == 'add_token')
async def add_token_func(call: CallbackQuery, state: FSMContext):
    text = f'Укажите {hbold("Стандартный")} токен.🔑\n\n{hbold("Как получить токен: 🗝")}\n' \
           f'1. Перейдите в личный кабинет WB ⏩ Профиль ⏩ Настройки ⏩ Доступ к API\n' \
           f'Или перейдите по ссылке: https://seller.wildberries.ru/supplier-settings/access-to-api\n' \
           f'2. Нажмите кнопку ▶"{hbold("Создать новый токен")}"\n' \
           f'3. Выберите тип токена {hbold("Стандартный 🗝")}, введите название магазина Ⓜ и нажмите кнопку ▶{hbold("Создать токен")}' \
           f'\n\nСозданный токен 🔑 вставьте ниже 👇'

    await call.message.edit_text(text, reply_markup=await cancel_add_token(),
                                 disable_web_page_preview=False)
    await state.set_state(EnterTokenState.enter_token)


@my_office_router.message(EnterTokenState.enter_token, F.text)
async def enter_token_func(message: Message, state: FSMContext):
    token = message.text
    in_db_token = await select_token(token)
    if in_db_token:
        await message.answer(text='Похоже этот токен уже зарегистрирован 🆘\n\nПопробуйте еще раз 🔄 или '
                                  'нажмите кнопку <b>Отмена</b> ❌', reply_markup=await cancel_add_token())
        return
    status_token = await ApiClient(api_key=token).check_standard_token()
    if status_token != 200:
        await message.answer('Похоже вы ввели не верный токен 🔑\n\nПопробуйте еще раз 🔄 или нажмите'
                             ' кнопку <b>Отмена</b> ❌',
                             reply_markup=await cancel_add_token())
        return
    await state.update_data(token=token)
    await message.answer('Придумайте имя вашего магазина 👇', reply_markup=await cancel_add_token())
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
    text = f'Настройка магазина:\n\n<b>{market.name_market}</b>\n\nЗдесь вы можете гибко настроить, как бот' \
           ' будет отвечать на ваши отзывы, в зависимости от их оценки.\n\n' \
           'Например:\nВы можете выбрать, чтобы на отзывы с оценкой 5 и 4 звезды бот отвечал в' \
           ' полностью автоматическом режиме. На все остальные отзывы [с оценками 3, 2, 1 звезда] бот' \
           ' будет создавать ответ, но будет присылать вам на согласование.\n\n' \
           'Ваш текущий режим ответов:\n\n' \
           f'1. ⭐️ - {"Автоматический" if market.auto_send_star_1 else "Полуавтоматический"}\n' \
           f'2. ⭐️⭐️ - {"Автоматический" if market.auto_send_star_2 else "Полуавтоматический"}\n' \
           f'3. ⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_3 else "Полуавтоматический"}\n' \
           f'4. ⭐️⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_4 else "Полуавтоматический"}\n' \
           f'5. ⭐️⭐️⭐️⭐️⭐️ - {"Автоматический" if market.auto_send_star_5 else "Полуавтоматический"}\n\n' \
           f'Если хотите изменить режим для одной или нескольких оценок — введите их через запятую ' \
           'Пример: 1, 2, 3'
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=await adit_mode_messages(market))
    else:
        await event.answer(text=text, reply_markup=await adit_mode_messages(market))
    await state.update_data(pk=callback_data.id)
    await state.set_state(EditStarsList.enter_list_stars)


@my_office_router.message(EditStarsList.enter_list_stars, F.text)
async def enter_list_stars_func(message: Message, state: FSMContext):
    list_stars = message.text
    data = await state.get_data()
    market = await select_market(int(data['pk']))
    list_stars = list_stars.replace(' ', '')
    if (len(list_stars) > 1 and ',' not in list_stars) or not ''.join(list_stars.split(',')).isdigit():
        await message.answer("Кажется вы ошиблись с вводом! 🆘\n\nПопробуйте еще раз 🔄")
        await check_first_market_func(message, FirstMarket(id=int(data['pk'])), state=state)
        return
    for star in list_stars.split(','):
        if int(star) > 5:
            await message.answer("Кажется вы ошиблись с вводом! 🆘\n\nПопробуйте еще раз 🔄")
            await check_first_market_func(message, FirstMarket(id=int(data['pk'])), state=state)
            return
        if int(star) == 1:
            market.auto_send_star_1 = True
        if int(star) == 2:
            market.auto_send_star_2 = True
        if int(star) == 3:
            market.auto_send_star_3 = True
        if int(star) == 4:
            market.auto_send_star_4 = True
        if int(star) == 5:
            market.auto_send_star_5 = True
    market.save()
    await check_first_market_func(message, FirstMarket(id=int(data['pk'])), state=state)


@my_office_router.callback_query(EditModeMessages.filter())
async def choose_mode_messages(call: CallbackQuery, callback_data: EditModeMessages, state: FSMContext):
    await state.clear()
    market = await select_market(callback_data.id)
    text = ''
    if callback_data.mode_mes == 'auto':
        market.auto_send_star_1 = True
        market.auto_send_star_2 = True
        market.auto_send_star_3 = True
        market.auto_send_star_4 = True
        market.auto_send_star_5 = True
        text = 'Вы изменили режим отправки сообщений на Автоматический 🤖'
    elif callback_data.mode_mes == 'not_auto':
        market.auto_send_star_1 = False
        market.auto_send_star_2 = False
        market.auto_send_star_3 = False
        market.auto_send_star_4 = False
        market.auto_send_star_5 = False
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
