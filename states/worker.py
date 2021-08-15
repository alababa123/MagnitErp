from aiogram.dispatcher.filters.state import StatesGroup, State

class worker(StatesGroup):
    job = State()
    no_job = State()
    start_job = State()
    stop_job = State()
    section_task = State()
    task_profile = State()
    input_task = State()
    reg_report = State()
    reg_declaration = State()
    input_declaration = State()
    photo_reg = State()
    zayavki = State()
    zayavki_into = State()
    zayavki_back = State()
    info = State()
    shift_deadlines = State()
    shift_deadlines_cause = State()