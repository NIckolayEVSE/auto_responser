import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aioredis import Redis

from tgbot.config import load_config, Config

from tgbot.middlewares.config import ConfigMiddleware
from tgbot.misc.logging import configure_logger
from tgbot.misc.set_bot_commands import set_commands
from tgbot.services import broadcaster

logger = logging.getLogger(__name__)


def scheduler_jobs(bot, config: Config):
    pass


async def on_startup(bot: Bot, admin_ids: list[int], config):
    await set_commands(bot)
    configure_logger(True)
    # await broadcaster.broadcast(bot, admin_ids, "Бот запущен")
    scheduler_jobs(bot, config)


def register_global_middlewares(dp: Dispatcher, config):
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))
    # dp.message.outer_middleware(CheckSubscribeMiddleware())
    # dp.callback_query.outer_middleware(CheckSubscribeMiddleware())


def setup_django():
    import django
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        'admin_panel.admin_panel.settings'
    )
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    django.setup()


async def main():
    setup_django()

    logger.info("Starting bot")
    config = load_config(".env")

    if config.misc.user_redis:
        redis = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db_fsm)
        storage = RedisStorage(redis=redis)
    else:
        storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)
    from tgbot.handlers.user import user_router
    from tgbot.handlers.time_send_handler import time_router
    from tgbot.handlers.my_offices import my_office_router
    from tgbot.handlers.inline import inline_router
    from tgbot.handlers.echo import echo_router
    from tgbot.handlers.admin import admin_router

    from tgbot.handlers.answer_to_trigger import trigger_router
    from tgbot.handlers.sheets_handler import sheets_router
    for router in [
        admin_router,
        user_router,
        my_office_router,
        time_router,
        sheets_router,
        # echo_router,
        trigger_router,
        inline_router,

    ]:
        dp.include_router(router)

    register_global_middlewares(dp, config)

    config.misc.scheduler.start()

    from tgbot.models.db_commands import create_super_user
    await create_super_user(config.misc.super_user_name, config.misc.super_user_pass)

    await on_startup(bot, config.tg_bot.admin_ids, config)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Возникла ошибка")
