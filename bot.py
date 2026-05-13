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

# Main Menu
main_menu = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="محصولات 🛍")],
    [KeyboardButton(text="حساب من 👤")]
  ],
  resize_keyboard=True
)

# Start
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

# Buttons
@dp.message(F.text == "محصولات 🛍")
async def products(message: Message):
  keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="1 گیگابایت - 1.2 دلار",
          callback_data="buy_1GB"
        )
      ],
      [
        InlineKeyboardButton(
          text="2 گیگابایت - 2.4 دلار",
          callback_data="buy_2GB"
        )
      ],
      [
        InlineKeyboardButton(
          text="5 گیگابایت - 5 دلار",
          callback_data="buy_5GB"
        )
      ],
      [
        InlineKeyboardButton(
          text="10 گیگابایت - 10 دلار",
          callback_data="buy_10GB"
        )
      ],
      [
        InlineKeyboardButton(
          text="20 گیگابایت - 15 دلار",
          callback_data="buy_20GB"
        )
      ]
    ]
  )

  await message.answer(
    "حجم مورد نظرتان را انتخاب کنید👇",
    reply_markup=keyboard
  )

# Buy Config
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
        InlineKeyboardMarkup(
          text="ارسال رسید 📤",
          callback_data="send_receipt"
        )
      ]
    ]
  )

  text = f"""
برای خرید {product['title']} باید مقدار {price} دلار
ارز تتر(USDT) یا تون کوین(TON) برای ما ارسال کنید.

💎 مقدار ارز:
USDT: {price}
TON: {ton_amount}

🟣 آدرس ولت TON و USDT (روی شبکه TON):
`{TON_WALLET}`

🟠 آدرس ولت USDT (روی شبکه TRC20):
`{TRC20_WALLET}`

توجه❗️
بعد از انتقال، با زدن دکمه ارسال رسید، تصویر رسید انتقال را ارسال کنید‌.
بعد از تایید انتقال توسط ادمین، کانفیگ خریداری شده برای شما ارسال خواهد شد.
"""
  await callback.message.answer(
    text,
    reply_markup=keyboard,
    parse_mode="Markdown"
  )

# Send Receipt
@dp.callback_query(F.data == "send_receipt")
async def ask_receipt(callback: CallbackQuery):
  await callback.message.answer(
    "لطفا تصویر رسید انتقال را ارسال کنید📷"
  )

# Receive Receipt
@dp.message(F.photo)
async def receipt(message: Message):
  if message.from_user.id not in pending_buy:
    return
  product = pending_buy[message.from_user.id]
  keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="تایید ✅",
          callback_data=f"approve_{message.from_user.id}"
        ),
        InlineKeyboardButton(
          text="رد ❌",
          callback_data=f"reject_{message.from_user.id}"
        )
      ]
    ]
  )
  username =message.from_user.username
  if username is None:
    username = "UNKNOWN"
  caption = f"""
خرید جدید 🛒

👤 نام:
{message.from_user.full_name}
🆔 نام کاربری:
@{username}
🆔 آیدی عددی:
{message.from_user.id}

📦 محصول:
{product}
"""
  await bot.send_photo(
    ADMIN_ID,
    message.photo[-1].file_id,
    caption=caption,
    reply_markup=keyboard
  )
  await message.answer(
    "رسید شما برای ادمین ارسال شد ✅/nپس از تایید رسید، کانفیگ خریداری شده ارسال خواهد شد./n/nاز صبر و شکیبایی شما متشکریم🌹"
  )

# Approve Receipt
@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):
  user_id = int(
    callback.data.replace("approve_", "")
  )
  with open("configs.txt", "r", encoding="utf-8") as file:
    configs = file.readlines()
  if len(configs) == 0:
    await callback.message.answer(
      "هیچ کانفیگ استفاده نشده ای وجود ندارد ❌"
    )
    return
  config = random.choice(configs).strip()
  await bot.send_message(
    user_id,
    f"""
پرداخت شما تایید شد ✅

کانفیگ شما 🔒
`{config}`
""",
    parse_mode="Markdown"
  )

# Reject Receipt
@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
  user_id = int(
    callback.data.replace("reject_", "")
  )
  await bot.send_message(
    user_id,
    "متاسفانه پرداخت شما تایید نشد ❌"
  )
  await callback.message.answer(
    "پرداخت رد شد"
  )

# My account
@dp.message(F.text == "حساب من 👤")
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
          text="بنر دعوت دوست 🎁",
          callback_data="invite"
        )
      ],
      [
        InlineKeyboardButton(
          text="بررسی دعوت و دریافت هدیه 📊",
          callback_data="check_invite"
        )
      ]
    ]
  )
  username = message.from_user.username
  if username is None:
    username = "UNKNOWN"
  text = f"""
حساب کاربری من

نام 👤
{message.from_user.full_name}
نام کاربری (یوزرنیم) 🆔
@{username}
دعوت موفق 👥
{invites} نفر

لینک دعوت 🔗
`{invite_link}`
"""
  await message.answer(
    text,
    reply_markup=keyboard,
    parse_mode="Markdown"
  )

# Invite Friend
@dp.callback_query(F.data == "invite")
async def invite(callback: CallbackQuery):
  invite_link = (
    f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"
  )
  text = f"""
با ربات پرشیا ویتوری میتونید با بهترین قیمت، کانفـیگ تهیه کنید. 💪

همچنین با دعوت ۱۰ نفر از دوستانتون از ما، ۲ گیگابایت کانفیگ هدیه بگیرید. 🎁

امکانات کانفیگ های ما:
بدون ضریب ❌
بدون محدودیت زمان ⏱️
بدون محدودیت کاربر 👥
بدون قطعی 🙅🏻‍♂
با بالاترین سرعت ( در حد استارلینک ) 🚗
و بهترن کیفیت اتصال 👌

برای مشاهده محصولات روی لینک زیر کلیک کنید 👇
{invite_link}
"""
  await callback.message.answer(text)

# Invitation review
@dp.callback_query(F.data == "check_invite")
async def check_invite(callback: CallbackQuery):
  user = get_user(callback.from_user.id)
  invites = user[3]
  if invites > 0 and invites % 10 == 0:
    await callback.message.answer(
      """
تبریک 🎉

شما 10 دعوت موفق داشتید.👌

بعد از بررسی ۲گیگابایت کانفیگ هدیه برای شما ارسال خواهد شد ✅
"""
    )

    await bot.send_message(
      ADMIN_ID,
      f"کاربر {callback.from_user.id} واجد دریافت هدیه شد."
    )
  else:
    remain = 10 - (invites % 10)
    await callback.message.answer(
      f"هنوز {remain} دعوت دیگر نیاز دارید تا 2 گیگابایت هدیه بگیرید 🎁"
    )

# Bot Start
async def main():
  print("Bot Started...")
  await dp.start_polling(bot)
asyncio.run(main())