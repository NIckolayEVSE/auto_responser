import openai


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
