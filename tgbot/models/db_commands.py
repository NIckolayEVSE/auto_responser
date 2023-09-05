import datetime

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from admin_panel.telebot.models import Client, WbToken, FeedbackAnswer, ManualGeneration, IncorrectWbToken, \
    GmailMarkets, AnswerTriggers


@sync_to_async()
def select_client(telegram_id):
    """
    Возвращает пользователя по телеграм ID
    """
    return Client.objects.filter(telegram_id=telegram_id).first()


@sync_to_async
def select_all_clients():
    return Client.objects.all()


@sync_to_async()
def create_client(username, telegram_id, url, name):
    """
    Создает пользователя
    """
    Client.objects.create(telegram_id=telegram_id, username=username, url=url, name=name)


@sync_to_async()
def create_super_user(username, password):
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, password=password)


@sync_to_async
def create_name_market_wb(user: Client, token, name_market):
    return WbToken.objects.create(user=user, token=token, name_market=name_market)


@sync_to_async
def select_token(token):
    return WbToken.objects.filter(token=token).first()


@sync_to_async
def select_market(pk):
    return WbToken.objects.filter(pk=pk).first()


@sync_to_async
def select_all_markets():
    return WbToken.objects.all()


@sync_to_async
def create_answer_feedback(market, rating, feedback, answer, feedback_id, name_feedback, answer_feed, link_photos=None,
                           link_feed=None):
    return FeedbackAnswer.objects.create(market=market, rating=rating, feedback=feedback, answer=answer,
                                         feedback_id=feedback_id, link_photos=link_photos, link_feedback=link_feed,
                                         name_item=name_feedback,
                                         day_answer=datetime.datetime.now(), answered_feed=answer_feed)


@sync_to_async
def select_feedback(feedback_id):
    return FeedbackAnswer.objects.filter(feedback_id=feedback_id).first()


@sync_to_async
def create_manual_feed(user: Client, feed):
    return ManualGeneration.objects.create(user=user, feedback=feed)


@sync_to_async
def select_manual_feed(pk):
    return ManualGeneration.objects.filter(pk=pk).first()


@sync_to_async
def create_incorrect_token(user, token):
    return IncorrectWbToken.objects.create(user=user, token=token)


@sync_to_async
def create_gmail(market, url):
    return GmailMarkets.objects.create(market=market, url=url)


@sync_to_async
def select_markets(user):
    return GmailMarkets.objects.filter(market__user=user)


@sync_to_async
def create_answer_triggers(market, feedback_id, text, answer, rating, name_item, link_item):
    return AnswerTriggers.objects.create(market=market, feedback_id=feedback_id, text=text, answer=answer,
                                         rating=rating, name_item=name_item, link_item=link_item)


@sync_to_async
def get_answer_triggers(feed_id):
    return AnswerTriggers.objects.filter(pk=feed_id).first()
