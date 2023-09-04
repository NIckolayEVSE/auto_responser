import asyncio
import os

import random
import re


from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.utils.markdown import hcode, hlink, hbold
from dotenv import load_dotenv
from environs import Env
from loguru import logger

from tgbot.config import load_config, Config
from tgbot.keyboards.inline import answer_to_feed_kb
from tgbot.keyboards.triggers_kb import trigger_kb

from tgbot.models.db_commands import select_all_clients, create_answer_triggers, create_answer_feedback

load_dotenv()


def setup_django():
    import django
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        'admin_panel.admin_panel.settings'
    )
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    django.setup()


async def scanning_answers_sheet(bot: Bot, config: Config):
    users = await select_all_clients()

    sheet = config.misc.google_table
    for user in users:
        if not user.on_scan:
            continue

        is_sub = await check_subscribed(user.telegram_id, "autoresponder")
        if not is_sub:
            logger.info(f'У пользователя {user.username} ID: {user.telegram_id} нет подписки')
            continue

        profile = await get_user_profile(user.telegram_id)
        if not profile['standard_token']:
            logger.info(f'У пользователя {user.username} ID: {user.telegram_id} нет токена')
            continue
        else:
            feedback = await get_feedbacks(profile['standard_token'])

        if not feedback:
            logger.info(f'Отзывов для пользователя {user.username} ID: {user.telegram_id} не найдено')
            continue
        logger.info(f'Найдено отзывов: {len(feedback["data"]["feedbacks"])} Для пользователя: {user.username}')
        try:
            feedbacks = feedback['data']['feedbacks']
        except KeyError:
            continue

        url = user.url
        if not url:
            continue

        ws = sheet.open_sheet(url)
        if not ws:
            await bot.send_message(chat_id=user.telegram_id, text='У вас не верный адрес таблицы.\n\n'
                                                                  'Измените его')
            continue
        triggers = await get_triggers(ws)

        for feed in feedbacks:

            is_trigger = await process_text(feed['text'].lower(), triggers, 'trigger')
            is_answer_trigger = await process_text(feed['text'].lower(), triggers, 'value')
            link_wb = "".join(["https://www.wildberries.ru/catalog/",
                               str(feed["productDetails"]["nmId"]),
                               "/feedbacks?imtId=",
                               str(feed["productDetails"]["imtId"]),
                               "#",
                               feed["id"]])

            text = f'{feed["productValuation"]} ⭐\n\n' \
                   f'Текст отзыва:\n\n' \
                   f'{hcode(feed["text"])}\n\n' \
                   f'{hlink("Ссылка на отзыв", link_wb)}'

            if is_trigger:
                if user.triggers_answer.filter(feedback_id=feed['id']):
                    continue
                if not is_answer_trigger:
                    text = f"Нашел отзыв с триггером <b>{is_trigger}</b>, но не нашел ответа"
                    await bot.send_message(chat_id=user.telegram_id, text=text)
                    continue
                text = f'У вас новый отзыв с {hbold("Триггером")}\n\n' \
                       f'{is_trigger}\n\n' + text \
                       + f"\n\nПредварительный ответ:\n\n{is_answer_trigger}"
                answer_triggers = await create_answer_triggers(user, feed['id'], feed['text'], is_answer_trigger)
                try:
                    await bot.send_message(chat_id=user.telegram_id, text=text,
                                           reply_markup=await trigger_kb(answer_triggers))
                    logger.info(f'Сообщение с триггером отправлено пользователю {user.username} ID: {user.telegram_id}')
                    await asyncio.sleep(0.1)
                    continue
                except (TelegramForbiddenError, TelegramBadRequest):
                    continue

            if user.feedback_answer.filter(feedback_id=feed['id']):
                continue

            recommendations = await take_recommendations(ws, feed["productDetails"]["nmId"])
            if recommendations:
                resul_feedback = await generate_answer(ws, feed['productValuation'], recommendations)
            else:
                resul_feedback = await generate_answer(ws, feed['productValuation'])

            if resul_feedback:
                if feed['productValuation'] in (1, 2, 3):
                    text = f'Новый ответ на отзыв 🆕\n\n' + text + \
                           f"\n\nПредварительный ответ:\n\n{resul_feedback}"

                    feed_to_kb = await create_answer_feedback(user, feed['productValuation'], feed['text'],
                                                              resul_feedback, feed['id'])
                    return await bot.send_message(chat_id=user.telegram_id, text=text,
                                                  reply_markup=await answer_to_feed_kb(feed_to_kb))

                else:
                    await send_feedback(profile['standard_token'], feed['id'], resul_feedback)

                    await create_answer_feedback(user, feed['productValuation'], feed['text'],
                                                 resul_feedback, feed['id'])

            else:
                await bot.send_message(chat_id=user.telegram_id, text=f'У вас не заполнены ответы для '
                                                                      f'{feed["productValuation"]} звезд')
                logger.info(f'Для пользователя {user.username} ID: {user.telegram_id} не заполнены ответы')
                continue
            try:
                text = f'Ответ на отзыв успешно отправлен\n\n' + text + f"\n\nПредварительный ответ:\n\n{resul_feedback}"
                await bot.send_message(chat_id=user.telegram_id, text=text)
                logger.info(f'Ответ на отзыв успешно отправлен для пользователя {user.username} ID: {user.telegram_id}')
                await asyncio.sleep(0.1)
            except (TelegramForbiddenError, TelegramBadRequest):
                continue


def process_text(text: str, dict_triggers: dict, output: str):
    sentences = re.split('[.!?]\s', text.lower())
    for sentence in sentences:
        for trigger, value in dict_triggers.items():
            if re.search(r'\b({})\b'.format(trigger.lower().strip()), sentence):
                return value if output == 'value' else trigger
    return False


async def get_triggers(ws):
    triggers = ws.get_worksheet(5)
    lol = triggers.get_all_values()
    dct_triggers = {key.lower().strip(): value for key, value in lol[1:]}
    return dct_triggers


async def generate_answer(ws, star: int, recommend: str = None):
    worksheet_dict = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}
    sheet_list = ws.get_worksheet(worksheet_dict.get(star))
    values_list = [random.choice(sheet_list.col_values(i)[1:]) if sheet_list.col_values(i)[1:] else ''
                   for i in range(1, 7)]
    if recommend:
        values_result = values_list[:5] + [recommend] + values_list[5:]
        return ' '.join(values_result).strip()
    return ' '.join(values_list).strip()


async def take_recommendations(ws, article: int):
    sheet_list = ws.get_worksheet(6)
    if not sheet_list:
        return ''
    values_list = sheet_list.get_all_values()[1:]
    dct_rec = {int(key): value + ' ' + value2 for key, value, value2 in values_list}
    return dct_rec.get(article)


async def send_answers_sheets(bot: Bot, config: Config):
    while True:
        logger.info('Start scan')
        await scanning_answers_sheet(bot, config)
        await asyncio.sleep(300)


async def main():
    logger.info("Starting auto_send")
    setup_django()
    env = Env()
    env.read_env(".env")
    bot = Bot(token=env.str("BOT_TOKEN"), parse_mode='HTML')
    config = load_config(".env")
    await send_answers_sheets(bot, config)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Остановка бота")
