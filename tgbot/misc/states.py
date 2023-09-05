from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    state_1 = State()


class EnterYourItemState(StatesGroup):
    item_feedback_state = State()


class EnterTokenState(StatesGroup):
    enter_token = State()
    enter_market_name = State()


class EditStarsList(StatesGroup):
    enter_list_stars = State()


class EnterMyTimeState(StatesGroup):
    enter_my_time = State()


class EddSignature(StatesGroup):
    enter_signature = State()


class EditSignature(StatesGroup):
    enter_signature = State()


class AddGmailState(StatesGroup):
    gmail = State()



