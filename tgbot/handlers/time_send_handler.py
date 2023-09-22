import re
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.keyboards.callback_data import DatesCallback, MyMarkets
from tgbot.keyboards.time_send_feed_kb import show_time_kb, days_statistic, back_stat, markets_kb, cancel_add_signature, \
    edit_signature_kb, feedback_choose_action_kb, settings_notifications
from tgbot.misc.some_data import date_list
from tgbot.misc.states import EnterMyTimeState, EddSignature, EditSignature
from tgbot.models.db_commands import select_client, select_market

time_router = Router()


@time_router.callback_query(F.data == 'settings_feeds')
async def settings_feeds(call: CallbackQuery):
    await call.message.edit_text('Выберите желаемую настройку',
                                 reply_markup=await settings_notifications())


@time_router.callback_query(F.data == 'time_send_feed')
async def time_send_feed_func(event: CallbackQuery | Message, state: FSMContext):
    text = 'Выбор режима уведомлений'
    dates = date_list()
    if isinstance(event, CallbackQuery):
        user = await select_client(event.message.chat.id)
    else:
        user = await select_client(event.from_user.id)
    if user.time_user:
        text = f'Выбор режима уведомлений\n\nУ вас выбрано собственное время <b>{user.time_user}</b>'
    data = await state.get_data()
    dates_del = data.get('dates', [user.time_notification])
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=await show_time_kb(dates_del, dates))
    else:
        await event.answer(text=text, reply_markup=await show_time_kb(dates_del, dates))


@time_router.callback_query(DatesCallback.filter())
async def get_dates(call: CallbackQuery, state: FSMContext, callback_data: DatesCallback):
    text = 'Выбор режима уведомлений'
    dates = date_list()
    user = await select_client(call.message.chat.id)

    data = await state.get_data()
    dates_del = data.get('dates', [user.time_notification])
    if callback_data.date:
        if callback_data.date in dates_del:
            dates_del.remove(callback_data.date)
        else:
            dates_del.clear()
            dates_del.append(callback_data.date)
        await state.update_data(dates_del=dates_del)
    if user.time_user is not None:
        text = f'Выбор режима уведомлений\n\nУ вас выбрано собственное время <b>{user.time_user}</b>'
    try:
        if dates_del[0] in date_list():
            user.time_user = None
            user.time_notification = dates_del[0]
        user.save()

        await call.message.edit_text(text=text, reply_markup=await show_time_kb(dates_del, dates))
    except IndexError:
        await call.answer('Выберите режим отправки уведомлений')


@time_router.callback_query(F.data == 'enter_self')
async def enter_self_time(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите ваше время\n\nНапример: 9-18')
    await state.set_state(EnterMyTimeState.enter_my_time)


@time_router.message(EnterMyTimeState.enter_my_time, F.text)
async def enter_my_time(message: Message, state: FSMContext):
    user_time = message.text
    time_pattern = r'^[0-9]-[0-9]{1,2}$'
    if not re.match(time_pattern, user_time):
        await message.answer('Кажется время введено в неправильном формате\n\n'
                             f'Ваш ввод: {user_time}\nВ каком формате время должно быть "9-21"')
        return
    user = await select_client(message.from_user.id)
    user.time_notification = 'my_time'
    user.time_user = user_time
    user.save()
    await state.clear()
    await time_send_feed_func(message, state)


@time_router.callback_query(F.data == 'statistic')
async def statistic(call: CallbackQuery):
    await call.message.edit_text("Статистика", reply_markup=await days_statistic())


@time_router.callback_query(F.data == 'stat_today')
async def stat_today(call: CallbackQuery):
    user = await select_client(call.message.chat.id)
    today = date.today()
    text = f'Количество ответов на отзывы за сегодня\n\n'
    markets = user.wb_token.all()
    for stars in reversed(range(1, 6)):
        to_day_feeds = 0
        for token in markets:
            to_day_feeds += token.feedback_answer.filter(day_answer__date=today, rating=stars,
                                                         answered_feed=True).count()
        text += f'{stars} {"⭐️" * stars}: <b>{"Нет ответов" if to_day_feeds == 0 else to_day_feeds}</b>\n'
    await call.message.edit_text(text=text, reply_markup=await back_stat())


@time_router.callback_query(F.data == 'stat_last_day')
async def stat_last_day(call: CallbackQuery):
    user = await select_client(call.message.chat.id)
    yesterday = date.today() - timedelta(days=1)
    text = f'Количество ответов на отзывы за вчера\n\n'
    markets = user.wb_token.all()
    for stars in reversed(range(1, 6)):
        to_day_feeds = 0
        for token in markets:
            to_day_feeds += token.feedback_answer.filter(day_answer__date=yesterday, rating=stars).count()
        text += f'{stars} {"⭐️" * stars}: <b>{"Нет ответов" if to_day_feeds == 0 else to_day_feeds}</b>\n'
    await call.message.edit_text(text=text, reply_markup=await back_stat())


@time_router.callback_query(F.data.in_(['stat_week', 'last_30']))
async def week_or_30_days(call: CallbackQuery):
    user = await select_client(call.message.chat.id)
    week_or_30 = date.today() - timedelta(days=7)
    text = f'Количество ответов на отзывы за 7 дней\n\n'
    markets = user.wb_token.all()
    if call.data == 'last_30':
        week_or_30 = date.today() - timedelta(days=30)
        text = f'Количество ответов на отзывы за 30 дней\n\n'
    for stars in reversed(range(1, 6)):
        to_day_feeds = 0
        for token in markets:
            to_day_feeds = token.feedback_answer.filter(day_answer__date__range=[week_or_30, date.today()],
                                                        rating=stars).count()
        text += f'{stars} {"⭐️" * stars}: <b>{"Нет ответов" if to_day_feeds == 0 else to_day_feeds}</b>\n'
    await call.message.edit_text(text=text, reply_markup=await back_stat())


@time_router.callback_query(F.data == 'sig_answers')
async def sig_answers(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await select_client(call.message.chat.id)
    cabinets = user.wb_token.all()
    text = 'Выберите магазин для которого добавить подпись'
    if not cabinets:
        text = 'У вас пока нет магазинов!'
    await call.message.edit_text(text=text, reply_markup=await markets_kb(cabinets))


@time_router.callback_query(MyMarkets.filter())
async def my_markets_func(event: CallbackQuery | Message, callback_data: MyMarkets, state: FSMContext):
    market = await select_market(callback_data.id)
    text = f'У вас нет подписи к ответам для это магазина <b>{market.name_market}</b>'
    if market.signature_for_answers:
        text = f'Текущая подпись к ответам\n\n<b>{market.signature_for_answers}</b>'
    await state.update_data(market_id=callback_data.id)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=await edit_signature_kb(market.signature_for_answers))
    else:
        await event.answer(text=text, reply_markup=await edit_signature_kb(market.signature_for_answers))


@time_router.callback_query(F.data == 'add_signature')
async def add_signature(call: CallbackQuery, state: FSMContext):
    text = 'Введите подпись'
    await call.message.edit_text(text=text, reply_markup=await cancel_add_signature())
    await state.set_state(EddSignature.enter_signature)


@time_router.message(EddSignature.enter_signature, F.text)
async def enter_signature(message: Message, state: FSMContext):
    signature = message.text
    data = await state.get_data()
    market = await select_market(data.get('market_id'))
    market.signature_for_answers = signature
    market.save()
    await message.answer(f'Подпись для магазина <b>{market.name_market}</b> Добавлена')
    await my_markets_func(message, MyMarkets(id=market.pk), state)
    await state.clear()


@time_router.callback_query(F.data == 'edit_signature')
async def edit_signature(call: CallbackQuery, state: FSMContext):
    text = 'Введите подпись для изменения'
    await call.message.edit_text(text=text, reply_markup=await cancel_add_signature())
    await state.set_state(EditSignature.enter_signature)


@time_router.message(EditSignature.enter_signature, F.text)
async def enter_signature(message: Message, state: FSMContext):
    signature = message.text
    data = await state.get_data()
    market = await select_market(data.get('market_id'))
    market.signature_for_answers = signature
    market.save()
    await message.answer(f'Подпись для магазина <b>{market.name_market}</b> Изменена')
    await my_markets_func(message, MyMarkets(id=market.pk), state)
    await state.clear()


@time_router.callback_query(F.data == 'sett_feed')
async def sett_feed_func(call: CallbackQuery):
    text = f'Настроить уведомления:\n\n' \
           'Возможность отключить/включить уведомления для автоматических ответов \n\n*по умолчанию <b>включены</b>'
    user = await select_client(call.message.chat.id)
    if user.feedbacks_send:
        text += '\n\nСтатус: <b>ВКЛЮЧЕНЫ</b>'
    else:
        text += '\n\nСтатус: <b>ОТКЛЮЧЕНЫ</b>'
    await call.message.edit_text(text=text, reply_markup=await feedback_choose_action_kb(user.feedbacks_send))


@time_router.callback_query(F.data.in_(["feed_true", "feed_false"]))
async def edit_feed_auto_send(call: CallbackQuery):
    user = await select_client(call.message.chat.id)
    text = f'Настроить уведомления:\n\n' \
           'Возможность отключить/включить уведомления для автоматических ответов \n\n*по умолчанию <b>включены</b>'
    if call.data == "feed_true":
        user.feedbacks_send = False
        text += '\n\nСтатус: <b>ОТКЛЮЧЕНЫ</b>'
    elif call.data == "feed_false":
        user.feedbacks_send = True
        text += '\n\nСтатус: <b>ВКЛЮЧЕНЫ</b>'
    user.save()
    await call.message.edit_text(text=text, reply_markup=await feedback_choose_action_kb(user.feedbacks_send))
