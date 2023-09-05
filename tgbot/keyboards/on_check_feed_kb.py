from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import AnswerFeedback, AnswerPhotoFeedback, NewGen


async def on_check_kb(feed_id, text, photos=None, gen=None, back=None):
    kb = InlineKeyboardBuilder()
    kb.button(text='🌐 Опубликовать', callback_data=AnswerFeedback(id=feed_id))
    kb.button(text='📝 Редактировать отзыв', switch_inline_query_current_chat=text)
    if gen is None:
        kb.button(text='🔄 Сгенерировать новый ответ', callback_data=NewGen(id=feed_id))
    if back is None:
        kb.button(text='❌ Не отвечать на отзыв', callback_data='do_not_answer')
    else:
        kb.button(text='🔙 Назад', callback_data='no_trig')
    if photos:
        kb.button(text='🖼️ Просмотреть фото отзыва', callback_data=AnswerPhotoFeedback(id=feed_id))
    return kb.adjust(2, 1).as_markup()
