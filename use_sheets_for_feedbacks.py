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

from tgbot.keyboards.on_check_feed_kb import on_check_kb
from tgbot.misc.api_wb_methods import ApiClient
from tgbot.config import load_config, Config

from tgbot.keyboards.triggers_kb import trigger_kb

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
    from tgbot.models.db_commands import create_answer_triggers, create_answer_feedback, select_all_markets

    markets = await select_all_markets()

    sheet = config.misc.google_table
    for market in markets:
        if not market.use_sheet or not market.on_scan:
            continue

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

        url = market.gmail_markets.first().url if market.gmail_markets.first() else False
        if not url:
            continue

        ws = sheet.open_sheet(url)
        if not ws:
            await bot.send_message(chat_id=market.user.telegram_id, text='У вас не верный url адрес таблицы.\n\n'
                                                                         'Измените его')
            continue
        triggers = await get_triggers(ws)
        count = 0
        for feed in feedbacks:
            is_trigger, is_answer_trigger = await asyncio.gather(
                process_text(feed['text'].lower(), triggers, 'trigger'),
                process_text(feed['text'].lower(), triggers, 'value')
            )
            link_wb = "".join(["https://www.wildberries.ru/catalog/",
                               str(feed["productDetails"]["nmId"]),
                               "/feedbacks?imtId=",
                               str(feed["productDetails"]["imtId"]),
                               "#",
                               feed["id"]])
            link_feed = "https://www.wildberries.ru/catalog/" + str(feed["productDetails"]["nmId"]) + '/detail.aspx'
            text = '\n'.join([f'{hbold("Оценка")}: {feed["productValuation"]} ⭐\n',
                              f'{hbold("Товар")}: {hlink(feed["productDetails"]["productName"], link_feed)}',
                              f'{hbold("Текст отзыва")}\n{hcode(feed["text"])}',
                              f'{hbold("Ссылка на отзыв")}: {link_wb}',
                              ])

            if is_trigger:
                if market.triggers.filter(feedback_id=feed['id']):
                    continue
                if not is_answer_trigger:
                    text = f"Нашел отзыв с триггером <b>{is_trigger}</b>, но не нашел ответа"
                    await bot.send_message(chat_id=market.user.telegram_id, text=text)
                    continue

                text = "\n".join([f'У вас новый отзыв с {hbold("Триггером")}',
                                  f'{is_trigger}\n', text,
                                  f"\n{hbold('Предварительный ответ')}:\n{is_answer_trigger}"])

                answer_triggers = await create_answer_triggers(market, feed['id'], feed['text'], is_answer_trigger,
                                                               feed["productValuation"],
                                                               feed["productDetails"]["productName"], link_feed,
                                                               is_trigger, link_wb
                                                               )

                try:
                    text_for_edit = "\n".join(
                        [f"tr Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={feed['id']}\n",
                         f'{is_answer_trigger}']
                    )
                    await bot.send_message(chat_id=market.user.telegram_id, text=text,
                                           reply_markup=await trigger_kb(answer_triggers, text_for_edit))
                    logger.info(
                        f'Сообщение с триггером отправлено пользователю {market.user.username} ID: {market.user.telegram_id}')
                    await asyncio.sleep(0.1)
                    continue
                except (TelegramForbiddenError, TelegramBadRequest):
                    continue

            if market.feedback_answer.filter(feedback_id=feed['id']):
                continue

            recommendations = await take_recommendations(ws, feed["productDetails"]["nmId"])
            if recommendations:
                resul_feedback = await generate_answer(ws, feed['productValuation'], recommendations)
            else:
                resul_feedback = await generate_answer(ws, feed['productValuation'])

            if resul_feedback:

                photo_link = None
                if feed["photoLinks"]:
                    photo_link = ",".join([link["fullSize"] for link in feed["photoLinks"]])
                count += 1

                if feed['productValuation'] in (1, 2, 3):
                    text = "\n".join(
                        [
                            f'Новый ответ на отзыв 🆕\n',
                            text,
                            f"\n{hbold('Предварительный ответ')}:',"
                            f"f'{resul_feedback}"
                        ]
                    )

                    await create_answer_feedback(market, feed['productValuation'], feed['text'],
                                                 resul_feedback, feed['id'],
                                                 feed["productDetails"]["productName"],
                                                 True, photo_link, link_feed, False
                                                 )
                    text_for_edit = "\n".join(
                        [f"Не удаляйте эту строку (редактируйте только текст отзыва) feedback_id={feed['id']}\n",
                         f'{resul_feedback}']
                    )
                    return await bot.send_message(chat_id=market.user.telegram_id, text=text,
                                                  reply_markup=await on_check_kb(feed['id'], text_for_edit, photo_link,
                                                                                 'not_gen'))

                else:
                    await ApiClient.send_feedback(market.token, feed['id'], resul_feedback)

                    await create_answer_feedback(market, feed['productValuation'], feed['text'],
                                                 resul_feedback, feed['id'], feed["productDetails"]["productName"],
                                                 True, photo_link, link_feed, False
                                                 )

            else:
                await bot.send_message(chat_id=market.user.telegram_id, text=f'У вас не заполнены ответы для '
                                                                             f'{feed["productValuation"]} звезд')
                logger.info(
                    f'Для пользователя {market.user.username} ID: {market.user.telegram_id} не заполнены ответы')
                continue
            try:
                text = "\n".join([f'Ответ на отзыв успешно отправлен ✅\n', text,
                                  f"\n{hbold('Предварительный ответ')}:\n{resul_feedback}"])
                await bot.send_message(chat_id=market.user.telegram_id, text=text)
                logger.info(
                    f'Ответ на отзыв успешно отправлен для пользователя {market.user.username} ID: {market.user.telegram_id}')
                await asyncio.sleep(0.1)
            except (TelegramForbiddenError, TelegramBadRequest):
                continue


async def process_text(text: str, dict_triggers: dict, output: str):
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
        logger.info('Start scan sheets')
        await scanning_answers_sheet(bot, config)
        await asyncio.sleep(600)


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
