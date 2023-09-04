from aiogram.filters.callback_data import CallbackData


class FirstMarket(CallbackData, prefix='market'):
    id: int


class EditModeMessages(CallbackData, prefix='mode'):
    id: int
    mode_mes: str


class DatesCallback(CallbackData, prefix='dates'):
    date: str


class MyMarkets(CallbackData, prefix='markets'):
    id: int


class AnswerFeedback(CallbackData, prefix='feedback'):
    id: str


class AnswerPhotoFeedback(CallbackData, prefix='photo'):
    id: str


class NewGen(CallbackData, prefix='gen'):
    id: str


class DeleteMarket(CallbackData, prefix='market_to_del'):
    id: int


class ManualCallback(CallbackData, prefix='manual'):
    id: int


class EmptyTextCallback(CallbackData, prefix='empty'):
    id: int


class EditEmptyTextCallback(CallbackData, prefix='edit_empty'):
    id: int
    mode: str


class EditModeGenerate(CallbackData, prefix='mode_gen'):
    id: int


class EditMode(CallbackData, prefix='edit_mode'):
    id: int
    mode: str


class MarketsTables(CallbackData, prefix='market_tables'):
    id: int
