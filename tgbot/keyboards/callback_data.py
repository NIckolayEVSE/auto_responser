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


class TriggerCallback(CallbackData, prefix='trigger'):
    id: int


class AnswerCallback(CallbackData, prefix='answer'):
    pk: int


class TriggerPagCallback(CallbackData, prefix='pag_trigger'):
    pk: int


class TriggerPagenCallback(CallbackData, prefix='pagen_trig'):
    st: int
    stop: int


class AnswerSheet(CallbackData, prefix='st_ans_pagen'):
    pk: int


class AnswerSheetPagen(CallbackData, prefix='pagen_answers'):
    st: int
    stop: int
