import asyncio
import openai
import os
from aiogram import Bot

from tgbot.config import Config
from tgbot.misc.gpt_answers import chat_gpt_ai


def markets_dict(market):
    return {
        1: market.auto_send_star_1,
        2: market.auto_send_star_2,
        3: market.auto_send_star_3,
        4: market.auto_send_star_4,
        5: market.auto_send_star_5
    }


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


async def send_error(bot: Bot, error_text=''):
    for chat_id in os.getenv('ADMINS'):
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
    # answer_text = ''
    # messages = return_dct_messages(text_for_system, client_feed)
    try:
        answer_text = ''.join(i async for i in chat_gpt_ai(client_feed))
        # async for i in response:
        #     answer_text += i
    except Exception as error:
        error_text = f'Чат GPT не отвечает возникла ошибка во время генерации: {error}'
        await send_error(bot, error_text)
    else:
        if answer_text:
            return answer_text
        else:
            error_text = 'Пустой ответ, нужно обновить доступ к GPT. Сейчас используется OPENAI GPT'
            await send_error(bot, error_text)
    return config.misc.open_ai.create_chat_completion(messages=return_dct_messages(client_feed))
    #     return config.misc.open_ai.create_chat_completion(client_feed)
    # if not answer_text:
    #     error_text = 'Пустой ответ, нужно обновить доступ к GPT. Сейчас используется OPENAI GPT'
    #     await send_error(bot, error_text)
    #     return config.misc.open_ai.create_chat_completion(client_feed)
    # return answer_text


class OpenAIGPT:
    def __init__(self, token):
        self.__token = token

    async def create_chat_completion(self, feedback: str = None, system_text: str = None, messages: list = None,
                                     model: str = "gpt-3.5-turbo") -> str:
        openai.api_key = self.__token
        if not messages:
            messages = [
                {"role": "system", "content": system_text},
                {"role": "user", "content": feedback},
            ]

        response = await openai.ChatCompletion.acreate(model=model, messages=messages)
        return response['choices'][0]['message']['content']
