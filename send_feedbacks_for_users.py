import asyncio
import os
from datetime import datetime

import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.utils.markdown import hcode, hlink, hbold
from dotenv import load_dotenv
from environs import Env
from loguru import logger

from tgbot.config import Config, load_config
from tgbot.keyboards.on_check_feed_kb import on_check_kb
from tgbot.misc.main_texts_and_funcs import generate_text_func

load_dotenv()


def setup_django():
    import django
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        'admin_panel.admin_panel.settings'
    )
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    django.setup()


async def send_answers(bot: Bot, config: Config):
    from tgbot.models.db_commands import create_answer_feedback, select_all_markets
    while True:
        await asyncio.sleep(300)
        markets = await select_all_markets()
        for market in markets:
            auto_check = {
                1: market.auto_send_star_1,
                2: market.auto_send_star_2,
                3: market.auto_send_star_3,
                4: market.auto_send_star_4,
                5: market.auto_send_star_5,
            }
            feedback = await get_feedbacks(market.token)

            if not feedback:
                logger.info(f'Отзывов для пользователя {market.user.username} ID: {market.user.username} не найдено')
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

                text = f'{hbold("Оценка")}: {feed["productValuation"]} ⭐\n' \
                       f'{hbold("Товар")}: {hlink(feed["productDetails"]["productName"], link_feed)}\n\n' \
                       f'{hbold("Текст отзыва")}:\n' \
                       f'{hcode(feed["text"])}\n\n'

                resul_feedback = await generate_text_func(feed['text'], bot, config)

                if not resul_feedback:
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
                    if market.user.feedbacks_send:
                        await send_feedback(market.token, feed['id'], result_text)
                        text = f'Ответ на отзыв успешно отправлен\n\n' + text + f"\n\n{hbold('Ответ')}:\n{result_text}"
                        await bot.send_message(chat_id=market.user.telegram_id, text=text)
                        answer_feed = True
                        market.save()
                    else:
                        await send_feedback(market.token, feed['id'], result_text)
                        answer_feed = True
                        market.save()
                else:
                    try:
                        text = f'Новый отзыв 🆕\n\n{hbold("Магазин")}: {market.name_market}\n' + text + f"{hbold('Ответ')}:\n{result_text}"
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


async def send_feedback(standard_token, feedback_id, text):
    url = 'https://feedbacks-api.wildberries.ru/api/v1/feedbacks'
    headers = {
        'Authorization': standard_token
    }
    params = {
        'id': feedback_id,
        'text': text,

    }
    async with aiohttp.ClientSession() as client:
        async with client.patch(url=url, headers=headers, json=params) as resp:
            if resp.status == 200:
                logger.info(f'Отзыв ОТПРАВЛЕН: Текст отзыва: {text} - ID отзыва: {feedback_id} ')
            else:
                logger.error(f'Текст ОШИБКИ отправки отзыва {await resp.json()}')


async def get_feedbacks(api_key):
    url = 'https://feedbacks-api.wildberries.ru/api/v1/feedbacks'
    headers = {
        'Authorization': api_key
    }
    params = {
        'isAnswered': 'false',
        'take': 100,
        'skip': 0
    }

    async with aiohttp.ClientSession() as client:
        async with client.get(url=url, headers=headers, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return False


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
        logger.error("Возникла ошибка")
