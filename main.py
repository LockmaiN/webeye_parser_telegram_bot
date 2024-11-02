import asyncio
import os
from app.parser import router
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv


async def main():
    load_dotenv()
    tg_bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(tg_bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Полінг скасовано")
