import logging
import os
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from openai import OpenAI
# просто импорт нужных библиотек да модулей
load_dotenv()
#а тут начинается самое интересное..
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
bot = Bot(
    token=os.getenv("TELEGRAM_TOKEN"),
    default=DefaultBotProperties(parse_mode="HTML")
) #все эти ключи и токены платные, кроме токена для бота в тг
router = Router()
storage = MemoryStorage()

class MaterialRequest(StatesGroup):
    topic = State()
    age_group = State()
    difficulty = State()
    format_type = State()

@router.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📚 Создать пособие")]],
        resize_keyboard=True
    )
    await message.answer("<b>👋 Методический помощник</b>", reply_markup=keyboard)

@router.message(lambda message: message.text == "📚 Создать пособие")
async def create_guide(message: types.Message, state: FSMContext):
    await message.answer("📝 Введите тему урока:")
    await state.set_state(MaterialRequest.topic)

@router.message(MaterialRequest.topic)
async def process_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="1-4 класс")],
            [types.KeyboardButton(text="5-9 класс")],
            [types.KeyboardButton(text="9-11 класс")]
        ],
        resize_keyboard=True
    )
    await message.answer("🏫 Выберите класс:", reply_markup=keyboard)
    await state.set_state(MaterialRequest.age_group) 
@router.message(MaterialRequest.age_group)
async def process_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🟢 Начальный")],
            [types.KeyboardButton(text="🟡 Средний")],
            [types.KeyboardButton(text="🔴 Продвинутый")]
        ],
        resize_keyboard=True
    )
    await message.answer("📊 Выберите уровень сложности:", reply_markup=keyboard)
    await state.set_state(MaterialRequest.difficulty)

@router.message(MaterialRequest.difficulty)
async def process_difficulty(message: types.Message, state: FSMContext):
    await state.update_data(difficulty=message.text)
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📖 Теория + задания")],
            [types.KeyboardButton(text="📝 Только практика")],
            [types.KeyboardButton(text="🧠 Тесты + ответы")]
        ],
        resize_keyboard=True
    )
    await message.answer("📄 Выберите формат материала:", reply_markup=keyboard)
    await state.set_state(MaterialRequest.format_type)

@router.message(MaterialRequest.format_type)
async def send_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    prompt = f"""
    Создай методическое пособие по теме "{data['topic']}".
    Класс: {data['grade']}, сложность: {data['difficulty']}, формат: {message.text}.
    Включи примеры и задания, соответствующие ФГОС.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # P.S тут можно использовать любую модель чата, тот же gpt 4, или мини 1o, просто 1o.. но там все зависит от купленного плана для API (
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        
        material = response.choices[0].message.content
        await message.answer(f"✅ <b>Готово!</b>\n\n{material}")
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка:</b>\n{str(e)}")
    await state.clear()
if __name__ == "__main__":
    from aiogram import Dispatcher
    
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
 #надеюсь этот код был прочитан) :)