import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from config import *
from database import add_user, get_user
from ton import get_ton_price

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

pending_buy = {}

# =========================
# منوی اصلی
# =========================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 محصولات")],
        [KeyboardButton(text="👤 حساب من")]
    ],
    resize_keyboard=True
)

# =========================
# استارت
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    args = message.text.split()

    invited_by = None

    if len(args) > 1:
        try:
            invited_by = int(args[1])
        except:
            pass

    if invited_by == message.from_user.id:
        invited_by = None

    add_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username,
        invited_by
    )

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu
    )

# =========================
# محصولات
# =========================

@dp.message(F.text == "🛍 محصولات")
async def products(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 گیگابایت - 1.2$",
                    callback_data="buy_1GB"
                )
            ],
            [
                InlineKeyboardButton(
                    text="2 گیگابایت - 2.4$",
                    callback_data="buy_2GB"
                )
            ],
            [
                InlineKeyboardButton(
                    text="5 گیگابایت - 5$",
                    callback_data="buy_5GB"
                )
            ],
            [
                InlineKeyboardButton(
                    text="10 گیگابایت - 10$",
                    callback_data="buy_10GB"
                )
            ],
            [
                InlineKeyboardButton(
                    text="20 گیگابایت - 15$",
                    callback_data="buy_20GB"
                )
            ]
        ]
    )

    await message.answer(
        "یکی از محصولات زیر را انتخاب کنید 👇",
        reply_markup=keyboard
    )

# =========================
# خرید محصول
# =========================

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery):

    product_key = callback.data.replace("buy_", "")

    product = PRODUCTS[product_key]

    price = product["price"]

    ton_price = await get_ton_price()

    ton_amount = round(price / ton_price, 2)

    pending_buy[callback.from_user.id] = product["title"]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 ارسال رسید",
                    callback_data="send_receipt"
                )
            ]
        ]
    )

    text = f"""
برای خرید {product['title']} باید مقدار {price} دلار
ارز TON یا USDT ارسال کنید.

💎 معادل TON:
{ton_amount} TON

🟦 آدرس TON:
{TON_WALLET}

🟩 آدرس USDT (TON):
{USDT_TON_WALLET}

🟥 آدرس USDT (TRC20):
{USDT_TRC20_WALLET}

توجه ❗️

بعد از انتقال با زدن دکمه ارسال رسید،
تصویر رسید انتقال را ارسال کنید.

بعد از تایید پرداخت،
کانفیگ خریداری شده برای شما ارسال خواهد شد.
"""

    await callback.message.answer(
        text,
        reply_markup=keyboard
    )

# =========================
# درخواست رسید
# =========================

@dp.callback_query(F.data == "send_receipt")
async def ask_receipt(callback: CallbackQuery):

    await callback.message.answer(
        "📷 لطفاً تصویر رسید را ارسال کنید"
    )

# =========================
# دریافت رسید
# =========================

@dp.message(F.photo)
async def receipt(message: Message):

    if message.from_user.id not in pending_buy:
        return

    product = pending_buy[message.from_user.id]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ تایید",
                    callback_data=f"approve_{message.from_user.id}"
                ),
                InlineKeyboardButton(
                    text="❌ رد",
                    callback_data=f"reject_{message.from_user.id}"
                )
            ]
        ]
    )

    username = message.from_user.username

    if username is None:
        username = "ندارد"

    caption = f"""
🛒 خرید جدید

👤 نام:
{message.from_user.full_name}

🆔 آیدی عددی:
{message.from_user.id}

📦 محصول:
{product}

🔗 یوزرنیم:
@{username}
"""

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=keyboard
    )

    await message.answer(
        "✅ رسید شما ارسال شد.\nلطفاً منتظر تایید ادمین باشید"
    )

# =========================
# تایید خرید
# =========================

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):

    user_id = int(
        callback.data.replace("approve_", "")
    )

    with open("configs.txt", "r", encoding="utf-8") as file:
        configs = file.readlines()

    if len(configs) == 0:

        await callback.message.answer(
            "❌ هیچ کانفیگی داخل فایل configs.txt وجود ندارد"
        )

        return

    config = random.choice(configs).strip()

    await bot.send_message(
        user_id,
        f"""
✅ پرداخت شما تایید شد

🔐 کانفیگ شما:

{config}
"""
    )

    await callback.message.answer(
        "✅ کانفیگ برای کاربر ارسال شد"
    )

# =========================
# رد خرید
# =========================

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):

    user_id = int(
        callback.data.replace("reject_", "")
    )

    await bot.send_message(
        user_id,
        "❌ پرداخت شما تایید نشد"
    )

    await callback.message.answer(
        "پرداخت رد شد"
    )

# =========================
# حساب من
# =========================

@dp.message(F.text == "👤 حساب من")
async def account(message: Message):

    user = get_user(message.from_user.id)

    invites = user[3]

    invite_link = (
        f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 دعوت دوست",
                    callback_data="invite"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 بررسی دعوت",
                    callback_data="check_invite"
                )
            ]
        ]
    )

    username = message.from_user.username

    if username is None:
        username = "ندارد"

    text = f"""
👤 حساب کاربری

📛 نام:
{message.from_user.full_name}

🔗 یوزرنیم:
@{username}

👥 دعوت موفق:
{invites} نفر

🔗 لینک دعوت:
{invite_link}
"""

    await message.answer(
        text,
        reply_markup=keyboard
    )

# =========================
# دعوت دوست
# =========================

@dp.callback_query(F.data == "invite")
async def invite(callback: CallbackQuery):

    invite_link = (
        f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"
    )

    text = f"""
🎁 لینک دعوت اختصاصی شما:

{invite_link}

با دعوت دوستانت جایزه بگیر 😍

هر 10 دعوت موفق = 2 گیگابایت رایگان
"""

    await callback.message.answer(text)

# =========================
# بررسی دعوت
# =========================

@dp.callback_query(F.data == "check_invite")
async def check_invite(callback: CallbackQuery):

    user = get_user(callback.from_user.id)

    invites = user[3]

    if invites > 0 and invites % 10 == 0:

        await callback.message.answer(
            """
🎉 تبریک!

شما 10 دعوت موفق داشتید.

2 گیگابایت هدیه بعد از بررسی
برای شما ارسال خواهد شد ✅
"""
        )

        await bot.send_message(
            ADMIN_ID,
            f"کاربر {callback.from_user.id} واجد دریافت هدیه شد"
        )

    else:

        remain = 10 - (invites % 10)

        await callback.message.answer(
            f"هنوز {remain} دعوت دیگر نیاز داری تا 2 گیگ رایگان بگیری 🎁"
        )

# =========================
# اجرای ربات
# =========================

async def main():

    print("Bot Started...")

    await dp.start_polling(bot)

asyncio.run(main())