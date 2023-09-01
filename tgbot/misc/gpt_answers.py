import hashlib
import json
import os
import random
import re
import uuid

import aiohttp
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad

from tgbot.misc.main_texts_and_funcs import return_dct_messages


async def get_gpt(model: str, messages: list, **kwargs):
    def encrypt(e):
        t = os.urandom(8).hex().encode('utf-8')
        n = os.urandom(8).hex().encode('utf-8')
        r = e.encode('utf-8')
        cipher = AES.new(t, AES.MODE_CBC, n)
        ciphertext = cipher.encrypt(pad(r, AES.block_size))
        return ciphertext.hex() + t.decode('utf-8') + n.decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Referer': 'https://chat.getgpt.world/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    data = {
        'messages': messages,
        'frequency_penalty': kwargs.get('frequency_penalty', 0),
        'max_tokens': kwargs.get('max_tokens', 4000),
        'model': model,
        'presence_penalty': kwargs.get('presence_penalty', 0),
        'temperature': kwargs.get('temperature', 1),
        'top_p': kwargs.get('top_p', 1),
        'stream': True,
        'uuid': str(uuid.uuid4())
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://chat.getgpt.world/api/chat/stream',
                                headers=headers, json={'signature': encrypt(json.dumps(data))}, ssl=False) as response:
            async for line in response.content:
                if b'delta' in line:
                    line_json = json.loads(line.decode('utf-8').split('data: ')[1])
                    if 'content' in line_json['choices'][0]['delta']:
                        yield line_json['choices'][0]['delta']['content']


async def ai_chat(messages: list):
    base = ''
    for message in messages:
        base += '%s: %s\n' % (message['role'], message['content'])
    base += 'assistant:'

    headers = {
        'authority': 'chat-gpt.org',
        'accept': '*/*',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://chat-gpt.org',
        'pragma': 'no-cache',
        'referer': 'https://chat-gpt.org/chat',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'message': base,
        'temperature': 1,
        'presence_penalty': 0,
        'top_p': 1,
        'frequency_penalty': 0
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://chat-gpt.org/api/text', headers=headers, json=json_data) as response:
            try:
                yield (await response.json())['message']
            except KeyError:
                return


async def chat_gpt_ai(client_feed: str, messages: list = None):
    chat = ''
    if messages is not None:
        messages = return_dct_messages(client_feed)
    for message in messages:
        chat += '%s: %s\n' % (message['role'], message['content'])
    chat += 'assistant: '

    async with aiohttp.ClientSession() as session:
        async with session.post('https://chatgpt.ai/') as response:
            nonce, post_id, _, bot_id = re.findall(
                r'data-nonce="(.*)"\n     data-post-id="(.*)"\n     data-url="(.*)"\n     data-bot-id="(.*)"\n     data-width',
                (await response.text()))[0]

    headers = {
        'authority': 'chatgpt.ai',
        'accept': '*/*',
        'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
        'cache-control': 'no-cache',
        'origin': 'https://chatgpt.ai',
        'pragma': 'no-cache',
        'referer': 'https://chatgpt.ai/gpt-4/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    data = {
        '_wpnonce': nonce,
        'post_id': post_id,
        'url': 'https://chatgpt.ai/gpt-4',
        'action': 'wpaicg_chat_shortcode_message',
        'message': chat,
        'bot_id': bot_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://chatgpt.ai/wp-admin/admin-ajax.php', headers=headers, data=data) as response:
            try:
                yield (await response.json())['data']
            except KeyError:
                return


async def deep_ai(messages: list):
    def md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[::-1]

    def get_api_key(user_agent: str) -> str:
        part1 = str(random.randint(0, 10 ** 11))
        part2 = md5(user_agent + md5(user_agent + md5(user_agent + part1 + "x")))

        return f"tryit-{part1}-{part2}"

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

    headers = {
        "api-key": get_api_key(user_agent),
        "user-agent": user_agent
    }

    files = {
        "chat_style": (None, "chat"),
        "chatHistory": (None, json.dumps(messages))
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.deepai.org/chat_response", headers=headers, data=files) as resp:
            resp.raise_for_status()
            async for chunk in resp.content.iter_any():
                yield chunk.decode()


async def get_h20_answers(messages: list):
    conversation = ''
    for message in messages:
        conversation += '%s: %s\n' % (message['role'], message['content'])

    conversation += 'assistant: '

    async with aiohttp.ClientSession() as session:
        response = await session.get("https://gpt-gm.h2o.ai/")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Referer": "https://gpt-gm.h2o.ai/r/jGfKSwU"
        }
        data = {
            "ethicsModalAccepted": "true",
            "shareConversationsWithModelAuthors": "true",
            "ethicsModalAcceptedAt": "",
            "activeModel": "h2oai/h2ogpt-gm-oasst1-en-2048-falcon-40b-v1",
            "searchEnabled": "true"
        }
        response = await session.post("https://gpt-gm.h2o.ai/settings", headers=headers, data=data)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://gpt-gm.h2o.ai/"
        }
        data = {
            "model": 'h2oai/h2ogpt-gm-oasst1-en-2048-open-llama-13b'
        }

        conversation_id_response = await session.post("https://gpt-gm.h2o.ai/conversation", headers=headers, json=data)
        conversation_id = await conversation_id_response.json()
        data = {
            "inputs": conversation,
            "parameters": {
                "temperature": 0.4,
                "truncate": 2048,
                "max_new_tokens": 1024,
                "do_sample": True,
                "repetition_penalty": 1.2,
                "return_full_text": False
            },
            "stream": True,
            "options": {
                "id": str(uuid.uuid4()),
                "response_id": str(uuid.uuid4()),
                "is_retry": False,
                "use_cache": False,
                "web_search_id": ""
            }
        }

        response = await session.post(f"https://gpt-gm.h2o.ai/conversation/{conversation_id['conversationId']}",
                                      headers=headers, json=data)
        response_text = await response.text()
        generated_text = response_text.replace("\n", "").split("data:")
        generated_text = json.loads(generated_text[-1])

    return generated_text["generated_text"]
