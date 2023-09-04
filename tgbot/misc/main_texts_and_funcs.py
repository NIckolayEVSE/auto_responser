import asyncio
import re

from aiogram import Bot
from aiogram.utils.markdown import hbold
from loguru import logger

from tgbot.config import Config
from tgbot.misc.gpt_answers import ai_chat


def set_market_autosend_state(market, state):
    market.auto_send_star_1 = state
    market.auto_send_star_2 = state
    market.auto_send_star_3 = state
    market.auto_send_star_4 = state
    market.auto_send_star_5 = state


def create_table(email_acc, name, config):
    url = config.misc.google_table.create_sheet(
        email_acc=email_acc,
        name=name
    )
    return url


def validate_email(email):
    pattern = r'\b[A-Za-z0-9._%+-]+@gmail\.com\Z'

    if re.fullmatch(pattern, email):
        return True
    else:
        return False


def set_market_stars(market, star_num):
    setattr(market, f'auto_send_star_{star_num}', True)


def validate_list_stars(list_stars: str) -> bool:
    list_stars = list_stars.replace(' ', '')
    if (len(list_stars) > 1 and ',' not in list_stars) or not ''.join(list_stars.split(',')).isdigit():
        return False
    for star in list_stars.split(','):
        if int(star) > 5:
            return False
    return True


def return_dct_messages(text_feedback, system_text: str = None) -> list[dict]:
    if system_text is None:
        system_text = 'I want you to act as a Менеджер маркетплейса and respond to a review in a way that' \
                      ' does not sound generated. Avoid using the word ' \
                      '"маркетплейс" in your response. Do not end the response with ' \
                      'the phrase "с уважением...". Keep in mind that on the marketplace, ' \
                      'the customer cannot contact the seller. Do not provide any recommendations. ' \
                      ' Use the following response template: ' \
                      '- Thank the customer for leaving a review\n' \
                      '- Emphasize any shortcomings, if present, and assure them that we will definitely address them\n' \
                      '- Highlight the advantages of the product, if applicable\n' \
                      '- Express gratitude for their review.\n' \
                      'The answer must be in Russian'
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": text_feedback},
    ]


async def send_error(bot: Bot, config: Config, error_text=''):
    for chat_id in config.tg_bot.admin_ids:
        await bot.send_message(chat_id, text=error_text)
        await asyncio.sleep(0.3)


# async def generate_text_func(text_for_system, client_feed, bot: Bot):
#     messages = return_dct_messages(text_for_system, client_feed)
#     answer_text = ''
#     try:
#         response = chat_gpt_ai(messages=messages)
#     except Exception as error:
#         await bot.send_message(chat_id=612075626, text=f'Чат GPT не отвечает: {error}')
#         await asyncio.sleep(0.3)
#         await bot.send_message(chat_id=417804053, text=f'Чат GPT не отвечает: {error}')
#         return
#     async for i in response:
#         answer_text += i
#     if not answer_text:
#         await bot.send_message(chat_id=612075626, text='Чат GPT не отвечает')
#         await asyncio.sleep(0.3)
#         await bot.send_message(chat_id=417804053, text='Чат GPT не отвечает')
#         return
#     return answer_text

async def generate_text_func(client_feed, bot: Bot, config: Config):
    try:
        # answer_text = ''.join(i async for i in ai_chat(return_dct_messages(client_feed)))
        answer_text = [i async for i in ai_chat(return_dct_messages(client_feed))][0]
    except Exception as error:
        error_text = f'Чат GPT не отвечает возникла ошибка во время генерации: {error}'
        await send_error(bot, config, error_text)
    else:
        if answer_text:
            logger.info('Используется кастомный GPT')
            return answer_text
        else:
            error_text = 'Пустой ответ, нужно обновить доступ к GPT. Сейчас используется OPENAI GPT'
            await send_error(bot, config, error_text)

    return await config.misc.open_ai.create_chat_completion(messages=return_dct_messages(client_feed))


def empty_text(market: bool):
    text = "\n".join(['Настройка режима ответа на отзывы без текста.\n',
                      'В данном разделе вы имеете возможность настроить функцию автоматического'
                      ' ответа на отзывы, которые не содержат текста.',
                      f'Обратите {hbold("внимание")}: данная настройка не будет применяться ко всем вашим магазинам одновременно.'
                      ' Ее нужно активировать для каждого магазина индивидуально.\n',
                      f'Текущий режим ответов: {hbold("Отвечать") if market else hbold("Не отвечать")}'
                      ])
    return text


def mode_edit_text(market):
    text = "\n".join([
        'В данном меню вы можете изменить метод генерации ответов на ваши табличные значения',
        f'{hbold("Магазин")}: {market.name_market}',
        f'{hbold("Статус")}: {"Табличная генерация" if market.use_sheet else "GPT генерация"}'
    ])
    return text
