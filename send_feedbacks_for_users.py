import asyncio
import os
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.utils.markdown import hcode, hlink, hbold
from dotenv import load_dotenv
from environs import Env
from loguru import logger

from tgbot.config import Config, load_config
from tgbot.keyboards.on_check_feed_kb import on_check_kb
from tgbot.misc.api_wb_methods import ApiClient
from tgbot.misc.main_texts_and_funcs import generate_text_func, send_error

load_dotenv()


def setup_django():
    import django
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        'admin_panel.admin_panel.settings'
    )
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    django.setup()


async def scanning_answers(bot: Bot, config: Config):
    from tgbot.models.db_commands import create_answer_feedback, select_all_markets
    markets = await select_all_markets()
    for market in markets:
        if market.use_sheet or not market.on_scan:
            continue
        auto_check = {i: getattr(market, f'auto_send_star_{i}') for i in range(1, 6)}
        feedback = await ApiClient.get_feedbacks(market.token)

        if not feedback:
            logger.info(f'Ошибка запроса отзывов клиента {market.user.username}')
            continue

        if feedback and not feedback['data']['feedbacks']:
            logger.info(f'Отзывов для пользователя {market.user.username} ID: {market.user.telegram_id} не найдено')
            continue

        try:
            feedbacks = feedback['data']['feedbacks']
        except KeyError:
            continue
        count = 0
        for feed in feedbacks:
            if market.feedback_answer.filter(feedback_id=feed['id']):
                continue

            link_feed = "https://www.wildberries.ru/catalog/" + str(feed["productDetails"]["nmId"]) + '/detail.aspx'

            text = "\n".join([f'{hbold("Оценка")}: {feed["productValuation"]} ⭐',
                              f'{hbold("Товар")}: {hlink(feed["productDetails"]["productName"], link_feed)}\n',
                              f'{hbold("Текст отзыва")}:',
                              f'{hcode(feed["text"]) if feed["text"] else hbold("У этого отзыва только оценка")}'])
            resul_feedback = await generate_text_func(feed['text'], bot, config)

            if not resul_feedback:
                text = 'Ошибка генерации отзыва в функции generate_text_func'
                await send_error(bot, config, error_text=text)
                continue

            result_text = resul_feedback + '\n\n' + market.signature_for_answers if market.signature_for_answers else resul_feedback

            times_dict = {
                'my_time': market.user.time_user,
                'time_day': '9-18',
                'full_day': '9-21'
            }

            now = datetime.now().time()
            time_range = 'my_time' if market.user.time_notification == 'my_time' else market.user.time_notification
            select_time = True
            if time_range != 'everyday':
                my_time = times_dict[time_range]
                start_time, end_time = map(int, my_time.split('-'))
                select_time = start_time <= now.hour <= end_time

            answer_feed = False
            if auto_check[feed['productValuation']] and select_time:
                # ответ на пустые отзывы
                if not market.send_empty_text and not feed["text"]:
                    logger.info(
                        f'Не отвечать на пустой текст отзыва. Магазин:{market.name_market} USERNAME {market.user.username}')
                    continue

                if market.user.feedbacks_send:
                    await ApiClient.send_feedback(market.token, feed['id'], result_text)

                    text = "\n".join([f'Ответ на отзыв успешно отправлен\n', text,
                                      f"\n\n{hbold('Ответ')}:\n{result_text}"])
                    await bot.send_message(chat_id=market.user.telegram_id, text=text)
                else:

                    await ApiClient.send_feedback(market.token, feed['id'], result_text)

                answer_feed = True
                market.save()
            else:
                try:
                    text = "\n".join([f'Новый отзыв 🆕\n', f'{hbold("Магазин")}: {market.name_market}\n', text,
                                      f'\n\n{hbold("Ответ")}:', f'{result_text}'])
                    text_for_edit = f"Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={feed['id']}\n\n{result_text}"
                    await bot.send_message(chat_id=market.user.telegram_id, text=text,
                                           reply_markup=await on_check_kb(feed['id'], text_for_edit,
                                                                          feed["photoLinks"]))
                    logger.info(
                        f'Ответ на отзыв на проверке у пользователя {market.user.username} ID: {market.user.telegram_id}')
                    await asyncio.sleep(0.1)

                except (TelegramForbiddenError, TelegramBadRequest):
                    continue

            photo_link = None
            if feed["photoLinks"]:
                photo_link = ",".join([link["fullSize"] for link in feed["photoLinks"]])
            count += 1
            await create_answer_feedback(market, feed['productValuation'], feed['text'], result_text,
                                         feed['id'], feed["productDetails"]["productName"], answer_feed, photo_link,
                                         link_feed)
        if count > 0:
            logger.info(
                f'Найдено отзывов: {count} Для пользователя: {market.user.telegram_id}')


async def send_answers(bot: Bot, config: Config):
    while True:
        logger.info('Start scan')
        await scanning_answers(bot, config)
        await asyncio.sleep(300)


async def main():
    logger.info("Starting auto_send")
    setup_django()
    env = Env()
    env.read_env(".env")
    bot = Bot(token=env.str("BOT_TOKEN"), parse_mode='HTML')
    config = load_config(".env")
    await send_answers(bot, config)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Остановка бота")
