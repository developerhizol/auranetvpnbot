# handlers/profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
import secrets

router = Router()

SUBSCRIPTION_DOMAIN = "streamnetvpn.bothost.tech"

user_delete_state = {}

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def regenerate_user_token(user_id: int) -> str:
    new_token = secrets.token_urlsafe(9)[:12]
    db.save_user_token(user_id, new_token)
    return new_token

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    token = db.get_user_token(user_id)
    if not token:
        token = secrets.token_urlsafe(9)[:12]
        db.save_user_token(user_id, token)
    
    profile_url = f"https://{SUBSCRIPTION_DOMAIN}/sub/{token}"
    device_limit = db.get_device_limit(user_id)
    active_devices = db.get_active_devices_count(user_id)
    
    text = (
        f"<b>Твой ключ для подключения:</b>\n"
        f"╰<code>{profile_url}</code>\n\n"
        f"{emoji('5447512780515078098', '📱')} <b>Устройства:</b> {active_devices}/{device_limit}\n\n"
        f"<b>Выберите интересующий раздел:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Мои платежи",
            callback_data="my_payments",
            icon_custom_emoji_id="5447421246172069841"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Мои устройства",
            callback_data="my_devices",
            icon_custom_emoji_id="5447512780515078098"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Перевыпустить ключ",
            callback_data="regenerate_key",
            icon_custom_emoji_id="5447611706496808621"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="back_to_menu"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "my_payments")
async def my_payments(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    conn = db._get_connection()
    rows = conn.execute("""
        SELECT date, amount FROM payments_log 
        WHERE user_id = ? 
        ORDER BY date DESC 
        LIMIT 3
    """, (user_id,)).fetchall()
    conn.close()
    
    if rows:
        payments_text = "\n".join([f"<b>{row['date'][:10]} — {row['amount']}₽</b>" for row in rows])
        text = f"{payments_text}"
    else:
        text = "<b>У вас нет платежей</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="profile"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "my_devices")
async def my_devices(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    devices = db.get_devices(user_id)
    
    if devices:
        devices_text = []
        for i, device in enumerate(devices):
            name = device.get('device_name')
            if not name:
                name = device.get('fingerprint', 'Неизвестное устройство')[:12]
            devices_text.append(f"<b>{i+1}: {name}</b>")
        text = "\n".join(devices_text)
    else:
        text = "<b>У вас нет устройств</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="profile"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "regenerate_key")
async def regenerate_key_prompt(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    text = (
        f"{emoji('5447611706496808621', '🔁')} <b>Перевыпуск ключа</b>\n\n"
        f"Перевыпуск нужен, чтобы отключить доступ других устройств к вашей подписке.\n\n"
        f"{emoji('5881702736843511327', '⚠️')} <b>Что произойдёт после перевыпуска:</b>\n"
        f"├ старый ключ перестанет работать\n"
        f"├ все подключённые устройства отключатся\n"
        f"├ список устройств обнулится\n"
        f"╰ нужно будет заново подключить новый ключ через бота"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Перевыпустить",
            callback_data="confirm_regenerate",
            icon_custom_emoji_id="5447611706496808621"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="profile"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm_regenerate")
async def confirm_regenerate(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    conn = db._get_connection()
    conn.execute("DELETE FROM device_fingerprints WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    new_token = regenerate_user_token(user_id)
    new_url = f"https://{SUBSCRIPTION_DOMAIN}/sub/{new_token}"
    
    text = (
        f"{emoji('5447242579827523388', '✅')} <b>Ключ перевыпущен</b>\n\n"
        f"Все старые подключения теперь недействительны. Подключите новый ключ через бота.\n\n"
        f"{emoji('5260730055880876557', '📄')} <b>Ваш новый ключ для подключения:</b>\n"
        f"╰<code>{new_url}</code>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Мои платежи",
            callback_data="my_payments",
            icon_custom_emoji_id="5447421246172069841"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Мои устройства",
            callback_data="my_devices",
            icon_custom_emoji_id="5447512780515078098"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Перевыпустить ключ",
            callback_data="regenerate_key",
            icon_custom_emoji_id="5447611706496808621"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="back_to_menu"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    from handlers.start import edit_main_menu
    user_id = callback.from_user.id
    first_name = callback.from_user.first_name
    username = callback.from_user.username
    
    await edit_main_menu(callback, user_id, first_name, username)
    await callback.answer()