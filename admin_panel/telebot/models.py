from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        abstract = True


class Client(CreatedModel):
    username = models.CharField(
        max_length=50,
        help_text='Username клиента',
        verbose_name='Username',
        blank=True,
        null=True
    )
    telegram_id = models.BigIntegerField(
        help_text='Telegram ID пользователя',
        verbose_name='Telegram ID'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Имя в Telegram',
        help_text='Имя в Telegram'
    )
    url = models.CharField(
        max_length=255,
        verbose_name='Ссылка на пользователя'
    )

    time_notification = models.CharField(
        default='everyday',
        verbose_name='Время отправки уведомлений'
    )
    time_user = models.CharField(
        null=True,
        verbose_name='Самостоятельное время поль-ля'
    )
    feedbacks_send = models.BooleanField(
        default=True,
        verbose_name='Вкл/выкл уведомления для автоматических ответов'
    )

    class Meta:
        verbose_name = 'Клиенты телеграмм бота'
        verbose_name_plural = 'Клиенты телеграмм бота'
        ordering = ('-created',)

    def __str__(self):
        return "{} ({})".format(self.username, self.telegram_id)


class IncorrectWbToken(models.Model):
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Токен WB',
        related_name='inc_wb_token'
    )
    token = models.CharField(
        max_length=150,
        verbose_name='Токен WB пользователя'
    )


class WbToken(models.Model):
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Токен WB',
        related_name='wb_token'
    )
    token = models.CharField(
        max_length=150,
        verbose_name='Токен WB пользователя'
    )
    signature_for_answers = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Подпись к ответам на отзывы'
    )
    name_market = models.CharField(
        max_length=150,
        null=True,
        verbose_name='Название магазина пользователя'
    )
    send_empty_text = models.BooleanField(
        default=True,
        verbose_name='Ответ на отзывы без текста'
    )
    use_sheet = models.BooleanField(
        default=False,
        verbose_name='Если True, используется Google Sheet'
    )
    auto_send_star_1 = models.BooleanField(
        default=False,
        verbose_name='False, то полуавтоматический режим'
    )
    auto_send_star_2 = models.BooleanField(
        default=False,
        verbose_name='False, то полуавтоматический режим'
    )
    auto_send_star_3 = models.BooleanField(
        default=False,
        verbose_name='False, то полуавтоматический режим'
    )
    auto_send_star_4 = models.BooleanField(
        default=False,
        verbose_name='False, то полуавтоматический режим'
    )
    auto_send_star_5 = models.BooleanField(
        default=False,
        verbose_name='False, то полуавтоматический режим'
    )
    on_scan = models.BooleanField(
        default=True,
        verbose_name='(T) сканирование вкл, (F) нет'
    )

    class Meta:
        verbose_name = 'Магазины телеграмм бота'
        verbose_name_plural = 'Магазины телеграмм бота'


class FeedbackAnswer(models.Model):
    market = models.ForeignKey(
        WbToken,
        on_delete=models.CASCADE,
        verbose_name='Магазин, которому принадлежит ответ',
        related_name='feedback_answer'
    )
    rating = models.IntegerField(
        verbose_name='Рейтинг'
    )
    feedback = models.TextField(
        verbose_name='Сам отзыв'
    )
    answer = models.TextField(
        verbose_name='Ответ на отзыв'
    )
    feedback_id = models.CharField(
        max_length=100,
        verbose_name='Id отзыва'
    )
    name_item = models.CharField(
        max_length=100,
        verbose_name='Название товара',
        null=True
    )
    link_photos = models.TextField(
        null=True,
        verbose_name='Ссылки на фото отзывов'
    )
    link_feedback = models.CharField(
        max_length=150,
        verbose_name='Ссылка на отзыв',
        null=True
    )
    day_answer = models.DateTimeField(
        verbose_name='Дата ответа на отзыв'
    )
    answered_feed = models.BooleanField(
        default=False,
        verbose_name='Состояние ответа на отзыв'
    )
    generated_mode = models.BooleanField(
        default=True,
        verbose_name='Режим генерации ответов GPT(T), Sheet(F)'
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        null=True,
        auto_now_add=True
    )


class ManualGeneration(models.Model):
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Ручная генерация',
        related_name='manual'
    )
    feedback = models.TextField(
        verbose_name='Текст от пользователя для генерации'
    )


class GmailMarkets(models.Model):
    market = models.ForeignKey(
        WbToken,
        on_delete=models.CASCADE,
        verbose_name='Магазин, которому url',
        related_name='gmail_markets'
    )
    url = models.CharField(
        null=True,
        max_length=100,
        verbose_name='Ссылка на таблицу магазина'
    )


class AnswerTriggers(models.Model):
    market = models.ForeignKey(
        WbToken,
        on_delete=models.CASCADE,
        verbose_name='Триггеры магазина',
        related_name='triggers'
    )

    feedback_id = models.CharField(
        max_length=100,
        verbose_name='Id отзыва'
    )
    text = models.TextField(
        verbose_name='Текст отзыва'
    )
    answer = models.TextField(
        verbose_name='Ответы'
    )
    rating = models.IntegerField(
        verbose_name='Рейтинг'
    )
    name_item = models.CharField(
        max_length=100,
        verbose_name='Название товара',
        null=True
    )
    link_item = models.CharField(
        max_length=150,
        verbose_name='Ссылка на товар',
        null=True
    )
    answered_feed = models.BooleanField(
        default=False,
        verbose_name='Состояние ответа на триггер'
    )
    trigger = models.CharField(
        null=True,
        max_length=20,
        verbose_name='Триггер'
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        null=True,
        auto_now_add=True
    )
    link_feed = models.CharField(
        max_length=150,
        verbose_name='Ссылка на отзыв',
        null=True
    )
