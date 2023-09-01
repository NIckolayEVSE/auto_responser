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
