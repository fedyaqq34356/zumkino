import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

running = False
task = None

seats1 = [
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(7)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(8)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(9)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(10)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(11)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(12)'
]
seats2 = [
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(15)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(16)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(6)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(3)',
    'body > div > div:nth-child(1) > div.container-cinema-hall > div.cinema-hall > div.seats > div > div:nth-child(5)'
]

async def handle_page(page, seats, window_num):
    url = 'https://multiplex.ua/cinema/kyiv/tsum#26092025'
    initial_xpath = 'xpath=/html/body/div[21]/div[4]/div/div[2]/div[5]/div/div[1]/a[2]'
    button_xpath = 'xpath=/html/body/div/div[2]/div/div/div[2]/div/button'
    
    logger.info(f"Window {window_num}: Navigating to {url}")
    await page.goto(url)
    logger.info(f"Window {window_num}: Clicking initial selector")
    await page.click(initial_xpath)
    logger.info(f"Window {window_num}: Waiting for hall to load")
    await page.wait_for_selector('div.container-cinema-hall', state='visible', timeout=30000)
    logger.info(f"Window {window_num}: Clicking seats")
    for i, seat in enumerate(seats):
        try:
            await page.wait_for_selector(seat, state='visible', timeout=5000)
            await page.click(seat)
            logger.info(f"Window {window_num}: Clicked seat {seat}")
            if i < len(seats) - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Window {window_num}: Failed to click {seat}: {e}")
    logger.info(f"Window {window_num}: Clicking button")
    await page.click(button_xpath)
    logger.info(f"Window {window_num}: Waiting 6:30 for timer end")
    await asyncio.sleep(390)

async def booking_loop(user_id):
    global running
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        while running:
            logger.info("Starting new cycle")
            context1 = await browser.new_context()
            page1 = await context1.new_page()
            context2 = await browser.new_context()
            page2 = await context2.new_page()
            await asyncio.gather(
                handle_page(page1, seats1, 1),
                handle_page(page2, seats2, 2)
            )
            await context1.close()
            await context2.close()
            logger.info("40s delay before next cycle")
            await asyncio.sleep(40)
        await browser.close()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Старт брон", callback_data="start_bron")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "start_bron")
async def start_bron(callback: types.CallbackQuery):
    global running, task
    if not running:
        running = True
        task = asyncio.create_task(booking_loop(callback.from_user.id))
        await callback.message.answer("Бронирование запущено.")
    else:
        await callback.message.answer("Уже запущено.")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel")
async def cancel(callback: types.CallbackQuery):
    global running, task
    if running:
        running = False
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await callback.message.answer("Бронирование остановлено.")
    else:
        await callback.message.answer("Не запущено.")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())