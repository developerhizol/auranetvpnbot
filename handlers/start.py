# handlers/start.py
from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
import locale
from database import db, get_moscow_time
from keyboards.main_menu import get_main_keyboard
from config import BOT_TOKEN

try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'ru_RU')
    except:
        pass

router = Router()
bot = Bot(token=BOT_TOKEN)

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def format_date(date: datetime) -> str:
    if not date:
        return "—"
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    return f"{date.day} {months[date.month]} {date.year}г."

async def edit_main_menu(target, user_id: int, first_name: str, username: str = None):
    user = db.get_user(user_id)
    is_new = user is None

    if is_new:
        db.create_user(user_id, first_name, username)
        gift_text = ""
    else:
        free_until = db.get_free_until(user_id)
        gift_text = ""

    is_active = db.is_subscription_active(user_id)
    plan = db.get_user_plan(user_id)
    
    user_emoji = emoji("5258011929993026890", "👨‍🦱")
    
    if is_active:
        status_emoji = emoji("5276229330131772747", "✅")
        sub_status = "активна"
        free_until = db.get_free_until(user_id)
        end_date_str = format_date(free_until) if free_until else "—"
        
        plan_names = {"free": "Free", "premium": "Premium"}
        plan_name = plan_names.get(plan, "Free")
        sub_line = f"╭ <b>Подписка:</b> <code>{sub_status}</code> {status_emoji}\n├ <b>Тариф:</b> <code>{plan_name}</code>\n╰ <b>До:</b> <code>{end_date_str}</code>"
    else:
        status_emoji = emoji("5276240711795107620", "⚠️")
        sub_status = "истекла"
        sub_line = f"<b>Подписка:</b> <code>{sub_status}</code> {status_emoji}"

    text = (
        f"<blockquote>{user_emoji} <code>{first_name}  [{user_id}]</code></blockquote>\n\n"
        f"{sub_line}"
        f"{gift_text}"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            reply_markup=get_main_keyboard(user_id),
            parse_mode="HTML"
        )
    else:
        await target.answer(
            text,
            reply_markup=get_main_keyboard(user_id),
            parse_mode="HTML"
        )

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    await edit_main_menu(message, user_id, first_name, username)