import datetime
from datetime import datetime
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from dateutil.relativedelta import *
from selenium.webdriver.chrome.options import Options
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.enums import ParseMode
import os
from aiogram import Bot
from dotenv import load_dotenv
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.clear_download_folder import Delete_files
import pandas as pd
import glob
from geopy.geocoders import Nominatim
from aiogram.fsm.context import FSMContext
from app.states import Car_numbers
import ast
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers import SchedulerAlreadyRunningError


router = Router()

load_dotenv()
tg_bot = Bot(token=os.getenv("TOKEN"))

PATH = r"/root/webeye_parse/download/"
PATH_TO_CONFIG_JSON_DATA = r"/root/webeye_parse\config\car_numbers_list.json"
PATH_TO_TIME_MANAGE_JSON_DATA = r"/root/webeye_parse\config\manage_time_list.json"

scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")


async def time_manage():
    car_time_manage_list = []
    if os.path.isfile(PATH_TO_TIME_MANAGE_JSON_DATA) and os.access(PATH_TO_TIME_MANAGE_JSON_DATA, os.R_OK):
        with open(PATH_TO_TIME_MANAGE_JSON_DATA, "r") as inputfile:
            car_time_manage_data = json.load(inputfile)
            car_time_manage_data = ast.literal_eval(car_time_manage_data)
            car_time_manage_list = car_time_manage_data

        active_time_list = []
        scheduler.remove_all_jobs()
        for index in range(len(car_time_manage_list)):
            active_time_list = car_time_manage_list[index].split(":")
            scheduler.add_job(send_message_info_cars_interval,
                              trigger="cron", hour=active_time_list[0], minute=active_time_list[1], second=0, replace_existing=True, misfire_grace_time=None, start_date=datetime.now())

        try:
            scheduler.start()
        except SchedulerAlreadyRunningError:
            pass


async def send_message_info_cars_interval():
    chrome_options = Options()
    prefs = {"download.default_directory": PATH}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(
        ChromeDriverManager().install()))

    driver.implicitly_wait(2)
    wait = WebDriverWait(driver, 30)
    tg_bot.send_message
    await tg_bot.send_message(int(os.getenv("TG_TEST_CHAT_ID")), f"Настав час пропарсити інформацію по машинах:")
    driver.get("https://www.webeye.eu/")
    driver.maximize_window()
    time.sleep(0.5)

    try:
        login_page = driver.find_element(By.CSS_SELECTOR,
                                         ".d-none.d-lg-block.btn.btn--sm.btn--primary")
        login_page.click()
        time.sleep(0.5)

        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#username"))).send_keys(os.getenv("LOGIN"))
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#password"))).send_keys(os.getenv("PASSWORD"))
        time.sleep(0.5)

        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#login_submit"))).click()
        time.sleep(0.5)
    except:
        print('User is already logged')

    time.sleep(0.5)

    cars_tracking_page = driver.find_element(By.CSS_SELECTOR,
                                             "li:nth-child(7) a:nth-child(1) div:nth-child(2) div:nth-child(1) div:nth-child(1)")
    cars_tracking_page.click()
    time.sleep(1.5)

    start_button = driver.find_element(By.CSS_SELECTOR,
                                       "#submitLekerdezes_subPageButton")
    start_button.click()
    time.sleep(10)

    Delete_files.delete_all_the_files_in_directory(PATH)

    export_to_excel_button = driver.find_element(By.CSS_SELECTOR,
                                                 "#excelLetoltes_subPage")
    export_to_excel_button.click()
    time.sleep(20)
    await tg_bot.send_message(int(os.getenv("TG_TEST_CHAT_ID")), f"Скоро все буде...")
    driver.quit()

    csv_file = glob.glob(os.path.join(PATH, "*.xlsx"))

    car_numbers_active_list = []
    if os.path.isfile(PATH_TO_CONFIG_JSON_DATA) and os.access(PATH_TO_CONFIG_JSON_DATA, os.R_OK):
        with open(PATH_TO_CONFIG_JSON_DATA, "r") as inputfile:
            car_numbers_data = json.load(inputfile)
            car_numbers_data = ast.literal_eval(car_numbers_data)
            car_numbers_active_list = car_numbers_data

    for file in csv_file:
        # Read the sheet with the name 'Sheet2'
        worksheet = pd.read_excel(file, sheet_name='Sheet2')

    worksheet.dropna(how='all', inplace=True)
    worksheet.drop(worksheet.iloc[:, 1:14], axis=1, inplace=True)
    worksheet.drop(worksheet.columns[[3, 4]], axis=1, inplace=True)
    worksheet.drop(index=[1, 2], inplace=True)

    # Extract car numbers list from excel
    car_numbers_excel_list = []
    for number in range(1, len(worksheet)):
        car_numbers_excel_list.append(worksheet.iloc[number, 0])

    # Remove charachters from car_numbers_excel_list
    for index in range(0, len(car_numbers_excel_list)):
        car_numbers_excel_list[index] = ''.join(
            c for c in car_numbers_excel_list[index] if c.isdigit())

    # Exclude car numbers, that not in excel file, but in config
    bad_car_numbers = []
    for car_number in car_numbers_active_list:
        if car_number not in car_numbers_excel_list:
            bad_car_numbers.append(car_number)

    for number in range(1, len(worksheet)):
        if any(car_number in worksheet.iloc[number, 0] for car_number in car_numbers_active_list):

            coordinates = str(worksheet.iloc[number, 1]) + \
                ", " + str(worksheet.iloc[number, 2])

            geolocator = Nominatim(user_agent="parser")
            location = geolocator.reverse(coordinates)

            await tg_bot.send_message(int(os.getenv("TG_TEST_CHAT_ID")), f"Адреса(локація) машини із номером <b>{worksheet.iloc[number, 0]}</b>:\n\n{location.address}" + "\n", parse_mode=ParseMode.HTML)
            time.sleep(2)

    # remove duplicates
    bad_car_numbers = list(dict.fromkeys(bad_car_numbers))
    for bad_cars in bad_car_numbers:
        await tg_bot.send_message(int(os.getenv("TG_TEST_CHAT_ID")), f"Немає у базі машини із номером <b>{bad_cars}</b>!!!" + "\n", parse_mode=ParseMode.HTML)


@router.message(CommandStart())
async def cmd_start_command(message: Message):
    startMessage = ""
    if (message.from_user.id == int(os.getenv("ADMIN_1")) or message.from_user.id == int(os.getenv("ADMIN_2"))):
        startMessage = "Привіт, " + f"{message.from_user.first_name}" + \
            "\n" + "Схоже ти адмін, тобі доступна команда  -  /config" + "\n" + \
            "\n" + "А також команда - /parse, для того щоб у будь-який момент пропарсити інформацію щодо машинок." + \
            "\n\nІ команда - /time:   для задання точного часу присилання сповіщень у групу."
    else:
        startMessage = "Привіт, " + f"{message.from_user.first_name}"

    await message.answer(startMessage)


@router.message(Command("config"))
async def cmd_config_command(message: Message, state: FSMContext):
    await state.set_state(Car_numbers.car_numbers_list)
    configMessage = ""
    if (message.from_user.id == int(os.getenv("ADMIN_1")) or message.from_user.id == int(os.getenv("ADMIN_2"))):
        if os.path.isfile(PATH_TO_CONFIG_JSON_DATA) and os.access(PATH_TO_CONFIG_JSON_DATA, os.R_OK):
            with open(PATH_TO_CONFIG_JSON_DATA, "r") as inputfile:
                car_numbers_data = json.load(inputfile)
                car_numbers_data = ast.literal_eval(car_numbers_data)

                text_str_car_numbers = ""
                for index in range(len(car_numbers_data)):
                    text_str_car_numbers += str(car_numbers_data[index]) + "\n"

            configMessage = f"Актуальний список номерів машин для відстеження:\n{text_str_car_numbers}" + \
                "\nВведи нижче новий список номерів:"
        else:
            configMessage = "На разі список порожній!" + "\n" + "Введи список номерів машин, які потрібно відстежувати(тільки цифри)" + \
                "\n" + "\n" + "Приклад списку: " + "\n" + "2849\n1874\n6832"
    else:
        configMessage = "Ой, а ти не схожий на адміна... Нахіба прописувати цю команду!"

    await message.answer(configMessage)


@router.message(Car_numbers.car_numbers_list, lambda message: message.text.isdigit() or message.text.__contains__('\n'))
async def cmd_cars_list(message: Message, state: FSMContext):
    await state.clear()

    if (message.text.__contains__(',') and any(char.isdigit() for char in message.text) == False):
        await message.answer("Вітаю, твій список порожній. Бот відпочиває..." + "\n" + "Переюзни команду конфіг")
    else:
        await message.answer("Чудово, список номерів машин для відстеження:" + "\n\n" + f"{message.text}")
        list_of_car_numbers = message.text.splitlines()

        json_string = json.dumps(list_of_car_numbers)
        with open(PATH_TO_CONFIG_JSON_DATA, "w") as outfile:
            json.dump(json_string, outfile)


@router.message(Car_numbers.car_numbers_list)
async def cmd_cars_list_invalid_input(message: Message):

    await message.answer("Ти ввів не цифри номера, а якусь ху*ню, нахіба ти це робиш?)" + "\n" + "Пробуй ще")


@router.message(Command("time"))
async def cmd_time_manage_command(message: Message, state: FSMContext):
    await state.set_state(Car_numbers.time_manage_list)
    timeMessage = ""
    if (message.from_user.id == int(os.getenv("ADMIN_1")) or message.from_user.id == int(os.getenv("ADMIN_2"))):
        if os.path.isfile(PATH_TO_TIME_MANAGE_JSON_DATA) and os.access(PATH_TO_TIME_MANAGE_JSON_DATA, os.R_OK):
            with open(PATH_TO_TIME_MANAGE_JSON_DATA, "r") as inputfile:
                time_manage_data = json.load(inputfile)
                time_manage_data = ast.literal_eval(time_manage_data)

                text_str_time_manage = ""
                for index in range(len(time_manage_data)):
                    text_str_time_manage += str(time_manage_data[index]) + "\n"

            timeMessage = f"Актуальний список годин:\n{text_str_time_manage}" + \
                "\nВведи нижче новий список часу:"
        else:
            timeMessage = "На разі список порожній!" + "\n" + "Введи список часу, коли потрібно присилати сповіщення в групу(години хвилини)" + \
                "\n" + "\n" + "Приклад списку: " + "\n" + \
                "8:00 (8:00 ранку)\n13:30 (13:30 дня)\n18:00 (18-та година вечора)"
    else:
        timeMessage = "Ой, а ти не схожий на адміна... Нахіба прописувати цю команду!"

    await message.answer(timeMessage)


@router.message(Car_numbers.time_manage_list, lambda message: message.text.isdigit() or message.text.__contains__(':') or message.text.__contains__('\n'))
async def cmd_cars_list(message: Message, state: FSMContext):
    await state.clear()

    if (message.text.__contains__(':') and any(char.isdigit() for char in message.text) == False):
        await message.answer("Вітаю, твій список порожній. Бот відпочиває..." + "\n" + "Переюзни команду time")
    else:
        await message.answer("Чудово, список точного часу, коли будуть приходити сповіщення в групу:" + "\n\n" + f"{message.text}")
        list_of_time_manage = message.text.splitlines()

        json_string = json.dumps(list_of_time_manage)
        with open(PATH_TO_TIME_MANAGE_JSON_DATA, "w") as outfile:
            json.dump(json_string, outfile)

        await time_manage()


@router.message(Car_numbers.time_manage_list)
async def cmd_time_manage_list_invalid_input(message: Message):

    await message.answer("Ти ввів не час, а якусь ху*ню, нахіба ти це робиш?)" + "\n" + "Пробуй ще")


@router.message(Command("parse"))
async def cmd_parse_command(message: Message):
    if (message.from_user.id == int(os.getenv("ADMIN_1")) or message.from_user.id == int(os.getenv("ADMIN_2"))):
        chrome_options = Options()
        prefs = {"download.default_directory": PATH}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(
            '--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options, service=ChromeService(
            ChromeDriverManager().install()))

        driver.implicitly_wait(2)
        wait = WebDriverWait(driver, 30)
        await message.answer("Починаю викачку ексельки...")
        driver.get("https://www.webeye.eu/")
        driver.maximize_window()
        time.sleep(0.5)

        try:
            login_page = driver.find_element(By.CSS_SELECTOR,
                                             ".d-none.d-lg-block.btn.btn--sm.btn--primary")
            login_page.click()
            time.sleep(0.5)

            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#username"))).send_keys(os.getenv("LOGIN"))
            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#password"))).send_keys(os.getenv("PASSWORD"))
            time.sleep(0.5)

            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#login_submit"))).click()
            time.sleep(0.5)
        except:
            print('User is already logged')

        time.sleep(0.5)

        cars_tracking_page = driver.find_element(By.CSS_SELECTOR,
                                                 "li:nth-child(7) a:nth-child(1) div:nth-child(2) div:nth-child(1) div:nth-child(1)")
        cars_tracking_page.click()
        time.sleep(1.5)

        start_button = driver.find_element(By.CSS_SELECTOR,
                                           "#submitLekerdezes_subPageButton")
        start_button.click()
        time.sleep(10)

        Delete_files.delete_all_the_files_in_directory(PATH)

        export_to_excel_button = driver.find_element(By.CSS_SELECTOR,
                                                     "#excelLetoltes_subPage")
        export_to_excel_button.click()
        time.sleep(20)
        await message.answer("Завантажив ексель файл, починаю його парсити...")
        driver.quit()

        csv_file = glob.glob(os.path.join(PATH, "*.xlsx"))

        car_numbers_active_list = []
        if os.path.isfile(PATH_TO_CONFIG_JSON_DATA) and os.access(PATH_TO_CONFIG_JSON_DATA, os.R_OK):
            with open(PATH_TO_CONFIG_JSON_DATA, "r") as inputfile:
                car_numbers_data = json.load(inputfile)
                car_numbers_data = ast.literal_eval(car_numbers_data)
                car_numbers_active_list = car_numbers_data

        worksheet = ""
        for file in csv_file:
            # Read the sheet with the name 'Sheet2'
            worksheet = pd.read_excel(file, sheet_name='Sheet2')

        worksheet.dropna(how='all', inplace=True)
        worksheet.drop(worksheet.iloc[:, 1:14], axis=1, inplace=True)
        worksheet.drop(worksheet.columns[[3, 4]], axis=1, inplace=True)
        worksheet.drop(index=[1, 2], inplace=True)

        # Extract car numbers list from excel
        car_numbers_excel_list = []
        for number in range(1, len(worksheet)):
            car_numbers_excel_list.append(worksheet.iloc[number, 0])

        # Remove charachters from car_numbers_excel_list
        for index in range(0, len(car_numbers_excel_list)):
            car_numbers_excel_list[index] = ''.join(
                c for c in car_numbers_excel_list[index] if c.isdigit())

        # Exclude car numbers, that not in excel file, but in config
        bad_car_numbers = []
        for car_number in car_numbers_active_list:
            if car_number not in car_numbers_excel_list:
                bad_car_numbers.append(car_number)

        for number in range(1, len(worksheet)):
            if any(car_number in worksheet.iloc[number, 0] for car_number in car_numbers_active_list):

                coordinates = str(worksheet.iloc[number, 1]) + \
                    ", " + str(worksheet.iloc[number, 2])

                geolocator = Nominatim(user_agent="parser")
                location = geolocator.reverse(coordinates)

                await message.answer(f"Адреса(локація) машини із номером <b>{worksheet.iloc[number, 0]}</b>:\n\n{location.address}" + "\n", parse_mode=ParseMode.HTML)
                time.sleep(2)

        # remove duplicates
        bad_car_numbers = list(dict.fromkeys(bad_car_numbers))
        for bad_cars in bad_car_numbers:
            await message.answer(f"Немає у базі машини із номером <b>{bad_cars}</b>!!!" + "\n", parse_mode=ParseMode.HTML)
    else:
        await message.answer("Ой, а ти не схожий на адміна... Нахіба прописувати цю команду!")
