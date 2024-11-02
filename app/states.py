from aiogram.fsm.state import StatesGroup, State


class Car_numbers(StatesGroup):
    car_numbers_list = State()
    time_manage_list = State()
