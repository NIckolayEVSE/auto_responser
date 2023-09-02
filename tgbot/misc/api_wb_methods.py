import aiohttp


class ApiClient:

    def __init__(self, api_key: str):
        self.token = api_key
        self.standard = "https://suppliers-api.wildberries.ru/"
        self.header = {
            "Authorization": self.token,
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    async def check_standard_token(self):
        url = self.standard + "public/api/v1/info"
        params = {
            'quantity': 0,
        }
        async with aiohttp.ClientSession() as client:
            async with client.get(url=url, headers=self.header, params=params) as resp:
                return resp.status

    @staticmethod
    async def send_feedback(standard_token, feedback_id, text):
        url = 'https://feedbacks-api.wildberries.ru/api/v1/feedbacks'
        headers = {
            'Authorization': standard_token
        }
        params = {
            'id': feedback_id,
            'text': text,

        }
        # async with aiohttp.ClientSession() as client:
        #     async with client.patch(url=url, headers=headers, json=params) as resp:
        #         if resp.status == 200:
        #             logger.info(f'Отзыв ОТПРАВЛЕН: Текст отзыва: {text} - ID отзыва: {feedback_id} ')
        #         else:
        #             logger.error(f'Текст ОШИБКИ отправки отзыва {await resp.json()}')

    @staticmethod
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
