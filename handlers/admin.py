# handlers/admin.py - ПОЛНЫЙ ФАЙЛ
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_ID
from database import db
from utils.admin_utils import get_servers_from_file, add_server_to_file, remove_server_from_file, clear_servers_file
from keyboards.admin_keyboards import (
    get_admin_main_keyboard, get_admin_back_keyboard, get_cancel_keyboard,
    get_confirm_keyboard, get_servers_management_keyboard, get_broadcast_choice_keyboard,
    get_give_subscription_plan_keyboard
)

router = Router()
admin_state = {}
pending_broadcast_buttons = {}
broadcast_type = {}
ADMIN_PRICE_STATE = {}

from handlers.payment import PLANS

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

PLUS_EMOJI_ID = "5818711397860642669"
THUMBS_UP_EMOJI_ID = "5465446274725610363"
CLICK_DOWN_NEW_EMOJI_ID = "6023566962624306038"
FAST_FORWARD_EMOJI_ID = "6037622221625626773"
CANCEL_EMOJI_ID = "5774077015388852135"
CHECK_EMOJI_NEW_ID = "5774022692642492953"
EYE_EMOJI_ID = "5253959125838090076"
QUESTION_EMOJI_ID = "5884510167986343350"
BROADCAST_START_EMOJI_ID = "5771868281212245617"
CHECK_MARK_EMOJI_ID = "5776375003280838798"
WARNING_EMOJI_ID = "5881702736843511327"
MAN_EMOJI_ID = "5904630315946611415"
STATS_EMOJI_ID = "5994378914636500516"
MAIL_EMOJI_ID = "5771695636411847302"
STATS_USERS_EMOJI_ID = "6032609071373226027"
STATS_MONEY_EMOJI_ID = "5987880246865565644"
STATS_SALES_EMOJI_ID = "6030664675253820292"
BAN_EMOJI_ID = "5258318620722733379"
ADMIN_PRICE_EMOJI_ID = "5974217466270716579"
ADMIN_SERVERS_EMOJI_ID = "5291980250811506652"
GIVE_SUBSCRIPTION_EMOJI_ID = "6023940002008799618"
TAKE_SUBSCRIPTION_EMOJI_ID = "6021852682262682598"
SERVERS_COUNT_EMOJI_ID = "5938539885907415367"
ADMIN_CROSS_EMOJI_ID = "5774077015388852135"
SERVERS_CLEAR_EMOJI_ID = "5774077015388852135"
SOLO_EMOJI_ID = "5258011929993026890"
PREMIUM_EMOJI_ID = "5258513401784573443"
FAMILY_EMOJI_ID = "5257963315258204021"
ADD_EMOJI_ID = "5775937998948404844"

async def send_safe_message(chat_id: int, text: str, reply_markup=None):
    from handlers.start import bot
    try:
        return await bot.send_message(chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML", link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception:
        return await bot.send_message(chat_id, text=text, reply_markup=reply_markup, parse_mode=None, link_preview_options=LinkPreviewOptions(is_disabled=True))

async def send_safe_photo(chat_id: int, photo: str, caption: str = "", reply_markup=None):
    from handlers.start import bot
    try:
        return await bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        return await bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode=None)

async def send_safe_video(chat_id: int, video: str, caption: str = "", reply_markup=None):
    from handlers.start import bot
    try:
        return await bot.send_video(chat_id, video=video, caption=caption, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        return await bot.send_video(chat_id, video=video, caption=caption, reply_markup=reply_markup, parse_mode=None)

async def parse_buttons_from_text(message: Message, lang: str):
    if not message.text:
        return None
    builder = InlineKeyboardBuilder()
    text = message.text
    entities = message.entities or []
    emoji_by_pos = {}
    for entity in entities:
        if entity.type == "custom_emoji":
            emoji_by_pos[entity.offset] = (entity.custom_emoji_id, entity.length)
    lines = text.split('\n')
    if not lines:
        return None
    color_map = {
        "зелёный": "success",
        "green": "success",
        "красный": "danger",
        "red": "danger",
        "синий": "primary",
        "blue": "primary"
    }
    current_pos = 0
    for original_line in lines:
        if not original_line.strip():
            current_pos += len(original_line) + 1
            continue
        line_start = current_pos
        current_pos += len(original_line) + 1
        line_stripped = original_line.strip()
        if '|' in line_stripped:
            parts = line_stripped.split('|')
        else:
            parts = [line_stripped]
        row_buttons = []
        for btn_part in parts:
            btn_part = btn_part.strip()
            if not btn_part:
                continue
            if ' — ' in btn_part:
                sep = ' — '
            elif ' - ' in btn_part:
                sep = ' - '
            else:
                continue
            btn_parts = btn_part.split(sep)
            if len(btn_parts) < 2:
                continue
            btn_text_raw = btn_parts[0].strip()
            url = btn_parts[1].strip()
            style = "primary"
            if len(btn_parts) >= 3:
                color_word = btn_parts[2].strip().lower()
                if color_word in color_map:
                    style = color_map[color_word]
            btn_pos_in_line = original_line.find(btn_text_raw)
            if btn_pos_in_line == -1:
                first_word = btn_text_raw.split()[0] if btn_text_raw else None
                if first_word:
                    btn_pos_in_line = original_line.find(first_word)
                if btn_pos_in_line == -1:
                    continue
            abs_pos = line_start + btn_pos_in_line
            custom_emoji_id = None
            clean_text = btn_text_raw
            for emoji_pos, (e_id, e_len) in emoji_by_pos.items():
                if abs_pos <= emoji_pos < abs_pos + len(btn_text_raw):
                    custom_emoji_id = e_id
                    clean_text = btn_text_raw[e_len:].strip()
                    break
            if not clean_text:
                clean_text = btn_text_raw
            if custom_emoji_id:
                button = InlineKeyboardButton(text=clean_text, url=url, style=style, icon_custom_emoji_id=custom_emoji_id)
            else:
                button = InlineKeyboardButton(text=clean_text, url=url, style=style)
            row_buttons.append(button)
        if row_buttons:
            builder.row(*row_buttons)
    return builder.as_markup() if builder.buttons else None

async def parse_buttons_from_ready_message(msg_data: dict, text: str, entities: list, lang: str):
    if not text:
        return None
    builder = InlineKeyboardBuilder()
    emoji_by_pos = {}
    if entities:
        for entity in entities:
            if entity.get("type") == "custom_emoji":
                offset = entity.get("offset", 0)
                length = entity.get("length", 1)
                custom_emoji_id = entity.get("custom_emoji_id")
                emoji_by_pos[offset] = (custom_emoji_id, length)
    lines = text.split('\n')
    if not lines:
        return None
    color_map = {
        "зелёный": "success",
        "green": "success",
        "красный": "danger",
        "red": "danger",
        "синий": "primary",
        "blue": "primary"
    }
    current_pos = 0
    for original_line in lines:
        if not original_line.strip():
            current_pos += len(original_line) + 1
            continue
        line_start = current_pos
        current_pos += len(original_line) + 1
        line_stripped = original_line.strip()
        if '|' in line_stripped:
            parts = line_stripped.split('|')
        else:
            parts = [line_stripped]
        row_buttons = []
        for btn_part in parts:
            btn_part = btn_part.strip()
            if not btn_part:
                continue
            if ' — ' in btn_part:
                sep = ' — '
            elif ' - ' in btn_part:
                sep = ' - '
            else:
                continue
            btn_parts = btn_part.split(sep)
            if len(btn_parts) < 2:
                continue
            btn_text_raw = btn_parts[0].strip()
            url = btn_parts[1].strip()
            style = "primary"
            if len(btn_parts) >= 3:
                color_word = btn_parts[2].strip().lower()
                if color_word in color_map:
                    style = color_map[color_word]
            btn_pos_in_line = original_line.find(btn_text_raw)
            if btn_pos_in_line == -1:
                first_word = btn_text_raw.split()[0] if btn_text_raw else None
                if first_word:
                    btn_pos_in_line = original_line.find(first_word)
                if btn_pos_in_line == -1:
                    continue
            abs_pos = line_start + btn_pos_in_line
            custom_emoji_id = None
            clean_text = btn_text_raw
            for emoji_pos, (e_id, e_len) in emoji_by_pos.items():
                if abs_pos <= emoji_pos < abs_pos + len(btn_text_raw):
                    custom_emoji_id = e_id
                    clean_text = btn_text_raw[e_len:].strip()
                    break
            if not clean_text:
                clean_text = btn_text_raw
            if custom_emoji_id:
                button = InlineKeyboardButton(text=clean_text, url=url, style=style, icon_custom_emoji_id=custom_emoji_id)
            else:
                button = InlineKeyboardButton(text=clean_text, url=url, style=style)
            row_buttons.append(button)
        if row_buttons:
            builder.row(*row_buttons)
    return builder.as_markup() if builder.buttons else None

async def parse_ready_message(message: Message) -> dict:
    if not message:
        return None
    result = {
        "type": "ready",
        "msg_type": "text",
        "chat_id": message.chat.id,
        "message_id": message.message_id,
        "reply_markup": None,
        "text": None,
        "photo": None,
        "video": None,
        "caption": None,
        "caption_entities": None,
        "entities": None
    }
    if message.reply_markup:
        try:
            result["reply_markup"] = message.reply_markup.model_dump()
        except Exception:
            result["reply_markup"] = None

    def serialize_entities(entities_list):
        if not entities_list:
            return None
        return [
            {
                "type": e.type,
                "offset": e.offset,
                "length": e.length,
                "url": getattr(e, "url", None),
                "custom_emoji_id": getattr(e, "custom_emoji_id", None)
            }
            for e in entities_list
        ]

    if message.text:
        result["msg_type"] = "text"
        result["text"] = message.text
        result["entities"] = serialize_entities(message.entities)
    elif message.photo:
        result["msg_type"] = "photo"
        result["photo"] = message.photo[-1].file_id
        result["caption"] = message.caption
        result["caption_entities"] = serialize_entities(message.caption_entities)
    elif message.video:
        result["msg_type"] = "video"
        result["video"] = message.video.file_id
        result["caption"] = message.caption
        result["caption_entities"] = serialize_entities(message.caption_entities)
    else:
        return None
    return result

async def send_ready_broadcast_message(chat_id: int, msg_data: dict):
    from handlers.start import bot
    try:
        msg_type = msg_data.get("msg_type", "text")
        reply_markup = None
        saved_markup = msg_data.get("reply_markup")
        if saved_markup:
            try:
                reply_markup = InlineKeyboardMarkup.model_validate(saved_markup)
            except Exception:
                reply_markup = None

        if reply_markup is None:
            if msg_type == "text":
                text = msg_data.get("text", "")
                entities = msg_data.get("entities")
                lang = "ru"
                buttons = await parse_buttons_from_ready_message(msg_data, text, entities, lang)
                if buttons:
                    reply_markup = buttons
            elif msg_type == "photo":
                caption = msg_data.get("caption", "")
                caption_entities = msg_data.get("caption_entities")
                lang = "ru"
                buttons = await parse_buttons_from_ready_message(msg_data, caption, caption_entities, lang)
                if buttons:
                    reply_markup = buttons
            elif msg_type == "video":
                caption = msg_data.get("caption", "")
                caption_entities = msg_data.get("caption_entities")
                lang = "ru"
                buttons = await parse_buttons_from_ready_message(msg_data, caption, caption_entities, lang)
                if buttons:
                    reply_markup = buttons

        if msg_type == "text":
            text = msg_data.get("text", "")
            entities = msg_data.get("entities")
            if entities:
                class FakeMessage:
                    def __init__(self, text, entities_data):
                        self.text = text
                        self.entities = []
                        for e in entities_data:
                            from aiogram.types import MessageEntity
                            entity = MessageEntity(type=e["type"], offset=e["offset"], length=e["length"], url=e.get("url"), custom_emoji_id=e.get("custom_emoji_id"))
                            self.entities.append(entity)
                fake_msg = FakeMessage(text, entities)
                html_text = await convert_message_to_html(fake_msg)
                return await send_safe_message(chat_id, html_text, reply_markup)
            else:
                return await send_safe_message(chat_id, text, reply_markup)
        elif msg_type == "photo":
            caption = msg_data.get("caption", "")
            caption_entities = msg_data.get("caption_entities")
            if caption_entities:
                class FakeMessage:
                    def __init__(self, text, entities_data):
                        self.text = text
                        self.entities = []
                        for e in entities_data:
                            from aiogram.types import MessageEntity
                            entity = MessageEntity(type=e["type"], offset=e["offset"], length=e["length"], url=e.get("url"), custom_emoji_id=e.get("custom_emoji_id"))
                            self.entities.append(entity)
                fake_msg = FakeMessage(caption, caption_entities)
                caption = await convert_message_to_html(fake_msg)
                return await send_safe_photo(chat_id, msg_data["photo"], caption, reply_markup)
        elif msg_type == "video":
            caption = msg_data.get("caption", "")
            caption_entities = msg_data.get("caption_entities")
            if caption_entities:
                class FakeMessage:
                    def __init__(self, text, entities_data):
                        self.text = text
                        self.entities = []
                        for e in entities_data:
                            from aiogram.types import MessageEntity
                            entity = MessageEntity(type=e["type"], offset=e["offset"], length=e["length"], url=e.get("url"), custom_emoji_id=e.get("custom_emoji_id"))
                            self.entities.append(entity)
                fake_msg = FakeMessage(caption, caption_entities)
                caption = await convert_message_to_html(fake_msg)
                return await send_safe_video(chat_id, msg_data["video"], caption, reply_markup)
        return None
    except Exception as e:
        print(f"Error sending ready broadcast: {e}")
        return None

async def convert_message_to_html(message) -> str:
    if not message.text:
        return ""
    text = message.text
    entities = message.entities or []
    if not entities:
        return text
    entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    result = text
    for entity in entities:
        try:
            entity_text = text[entity.offset:entity.offset + entity.length]
            if entity.type == "bold":
                replacement = f"<b>{entity_text}</b>"
            elif entity.type == "italic":
                replacement = f"<i>{entity_text}</i>"
            elif entity.type == "underline":
                replacement = f"<u>{entity_text}</u>"
            elif entity.type == "strikethrough":
                replacement = f"<s>{entity_text}</s>"
            elif entity.type == "code":
                replacement = f"<code>{entity_text}</code>"
            elif entity.type == "pre":
                replacement = f"<pre>{entity_text}</pre>"
            elif entity.type == "text_link":
                replacement = f'<a href="{entity.url}">{entity_text}</a>'
            elif entity.type == "custom_emoji":
                replacement = f'<tg-emoji emoji-id="{entity.custom_emoji_id}">{entity_text}</tg-emoji>'
            else:
                continue
            result = result[:entity.offset] + replacement + result[entity.offset + entity.length:]
        except Exception as e:
            print(f"Error: {e}")
            continue
    return result

async def show_broadcast_preview(source_message: Message, user_id: int, lang: str):
    if user_id not in pending_broadcast_buttons:
        await source_message.answer("Ошибка: данные рассылки не найдены.")
        return
    data = pending_broadcast_buttons[user_id]
    msg_data = data.get("message_data")
    keyboard = data.get("buttons")
    b_type = data.get("type", "custom")
    if not msg_data:
        await source_message.answer("Ошибка: данные сообщения не найдены.")
        return
    preview_text = f"{emoji(EYE_EMOJI_ID, '👁️')} <b>Предпросмотр вашей рассылки:</b>" if lang == "ru" else f"{emoji(EYE_EMOJI_ID, '👁️')} <b>Broadcast preview:</b>"
    await source_message.answer(preview_text, parse_mode="HTML")
    try:
        if b_type == "ready":
            await send_ready_broadcast_message(source_message.chat.id, msg_data)
        else:
            if msg_data["type"] == "text":
                if msg_data.get("entities"):
                    class FakeMessage:
                        def __init__(self, text, entities):
                            self.text = text
                            self.entities = entities
                    fake_msg = FakeMessage(msg_data["text"], msg_data["entities"])
                    html_text = await convert_message_to_html(fake_msg)
                    await send_safe_message(source_message.chat.id, html_text, keyboard)
                else:
                    await send_safe_message(source_message.chat.id, msg_data["text"], keyboard)
            elif msg_data["type"] == "photo":
                caption = msg_data.get("caption", "")
                if msg_data.get("caption_entities"):
                    class FakeMessage:
                        def __init__(self, text, entities):
                            self.text = text
                            self.entities = entities
                    fake_msg = FakeMessage(caption, msg_data["caption_entities"])
                    caption = await convert_message_to_html(fake_msg)
                    await send_safe_photo(source_message.chat.id, msg_data["photo"], caption, keyboard)
            elif msg_data["type"] == "video":
                caption = msg_data.get("caption", "")
                if msg_data.get("caption_entities"):
                    class FakeMessage:
                        def __init__(self, text, entities):
                            self.text = text
                            self.entities = entities
                    fake_msg = FakeMessage(caption, msg_data["caption_entities"])
                    caption = await convert_message_to_html(fake_msg)
                    await send_safe_video(source_message.chat.id, msg_data["video"], caption, keyboard)
    except Exception as e:
        print(f"Preview error: {e}")
        await source_message.answer(f"Ошибка: {e}")
        return
    confirm_text = f"{emoji(QUESTION_EMOJI_ID, '❓')} <b>Вы точно хотите разослать это сообщение всем пользователям бота?</b>" if lang == "ru" else f"{emoji(QUESTION_EMOJI_ID, '❓')} <b>Are you sure you want to send this message to all users?</b>"
    await source_message.answer(confirm_text, reply_markup=get_confirm_keyboard("confirm_broadcast", "cancel_broadcast"), parse_mode="HTML")

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        f"{emoji(MAN_EMOJI_ID, '👨‍💻')} <b>Админ панель</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    stats = db.get_stats()
    await message.answer(
        f"{emoji(STATS_EMOJI_ID, '📊')} <b>Пользователи:</b> {stats['total_users']}",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(MAN_EMOJI_ID, '👨‍💻')} <b>Админ панель</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    stats = db.get_stats()
    text = (
        f"{emoji(STATS_USERS_EMOJI_ID, '👥')} <b>Пользователи</b>\n"
        f"• За день: {stats['today_users']}\n"
        f"• За неделю: {stats['week_users']}\n"
        f"• За месяц: {stats['month_users']}\n"
        f"• Всего: {stats['total_users']}\n\n"
        f"{emoji(STATS_MONEY_EMOJI_ID, '💰')} <b>Пополнения</b>\n"
        f"• За день: {stats['today_payments']} ₽\n"
        f"• За неделю: {stats['week_payments']} ₽\n"
        f"• За месяц: {stats['month_payments']} ₽\n"
        f"• Всего: {stats['total_payments']} ₽\n\n"
        f"{emoji(STATS_SALES_EMOJI_ID, '💎')} <b>Продажи премиума</b>\n"
        f"• За день: {stats['today_sales']} ₽\n"
        f"• За неделю: {stats['week_sales']} ₽\n"
        f"• За месяц: {stats['month_sales']} ₽\n"
        f"• Всего: {stats['total_sales']} ₽"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(BAN_EMOJI_ID, '🔒')} <b>Отправьте ID пользователя для бана:</b>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "ban", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_unban")
async def admin_unban_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(CHECK_EMOJI_NEW_ID, '🔓')} <b>Отправьте ID пользователя для разбана:</b>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "unban", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_give_subscription")
async def admin_give_subscription_plan(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(GIVE_SUBSCRIPTION_EMOJI_ID, '👑')} <b>Выберите тариф для выдачи:</b>",
        reply_markup=get_give_subscription_plan_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_give_plan_"))
async def admin_give_plan_selected(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    plan = callback.data.split("_")[3]
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(GIVE_SUBSCRIPTION_EMOJI_ID, '👑')} <b>Выбран тариф: {plan.capitalize()}</b>\n\nОтправьте ID пользователя для выдачи подписки:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "give_subscription", "plan": plan, "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_take_subscription")
async def admin_take_subscription_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(TAKE_SUBSCRIPTION_EMOJI_ID, '👎')} <b>Отправьте ID пользователя для забора подписки:</b>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "take_subscription", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_price")
async def admin_price_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    
    text = f"<b>Выберите тариф:</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Solo",
            callback_data="admin_price_plan_solo",
            style="primary",
            icon_custom_emoji_id="5258011929993026890"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Premium",
            callback_data="admin_price_plan_premium",
            style="primary",
            icon_custom_emoji_id="5258513401784573443"
        ),
        InlineKeyboardButton(
            text="Family",
            callback_data="admin_price_plan_family",
            style="primary",
            icon_custom_emoji_id="5257963315258204021"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="admin_panel"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_price_plan_"))
async def admin_price_plan_selected(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    
    plan_key = callback.data.split("_")[3]
    ADMIN_PRICE_STATE[callback.from_user.id] = {"plan": plan_key}
    
    await callback.answer()
    
    text = f"<b>Выберите срок тарифа:</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="1 месяц",
            callback_data=f"admin_price_duration_{plan_key}_month"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="3 месяца",
            callback_data=f"admin_price_duration_{plan_key}_3months"
        ),
        InlineKeyboardButton(
            text="6 месяцев",
            callback_data=f"admin_price_duration_{plan_key}_6months"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="admin_price"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_price_duration_"))
async def admin_price_duration_selected(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    
    parts = callback.data.split("_")
    plan_key = parts[3]
    duration_key = parts[4]
    
    if callback.from_user.id not in ADMIN_PRICE_STATE:
        ADMIN_PRICE_STATE[callback.from_user.id] = {}
    
    ADMIN_PRICE_STATE[callback.from_user.id].update({
        "plan": plan_key,
        "duration": duration_key
    })
    
    await callback.answer()
    
    duration_labels = {
        "month": "1 месяц",
        "3months": "3 месяца",
        "6months": "6 месяцев"
    }
    
    plan_names = {
        "solo": "Solo",
        "premium": "Premium",
        "family": "Family"
    }
    
    text = (
        f"<b>Тариф: {plan_names.get(plan_key, plan_key.capitalize())}</b>\n"
        f"<b>Срок: {duration_labels.get(duration_key, duration_key)}</b>\n\n"
        f"{emoji('5974217466270716579', '💰')} <b>Введите новую цену (только число):</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    
    admin_state[callback.from_user.id] = {
        "action": "price_with_plan",
        "msg_id": callback.message.message_id,
        "chat_id": callback.message.chat.id
    }

@router.message(F.text, lambda message: admin_state.get(message.from_user.id, {}).get("action") == "price_with_plan")
async def handle_admin_price_with_plan(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    state = admin_state.get(user_id, {})
    
    try:
        new_price = int(message.text.strip())
        if new_price < 1:
            await message.answer(f"{emoji('5774077015388852135', '❌')} <b>Цена должна быть больше 0!</b>", parse_mode="HTML")
            return
        
        price_state = ADMIN_PRICE_STATE.get(user_id, {})
        plan_key = price_state.get("plan")
        duration_key = price_state.get("duration")
        
        if not plan_key or not duration_key:
            await message.answer(f"{emoji('5774077015388852135', '❌')} <b>Ошибка: не выбран тариф или срок</b>", parse_mode="HTML")
            return
        
        price_key = f"price_{duration_key}"
        if plan_key in PLANS and price_key in PLANS[plan_key]:
            PLANS[plan_key][price_key] = new_price
            
            duration_labels = {
                "month": "1 мес.",
                "3months": "3 мес.",
                "6months": "6 мес."
            }
            
            plan_names = {
                "solo": "Solo",
                "premium": "Premium",
                "family": "Family"
            }
            
            await message.answer(
                f"{emoji('5774022692642492953', '✅')} <b>Цена изменена!</b>\n\n"
                f"<b>Тариф:</b> {plan_names.get(plan_key, plan_key.capitalize())}\n"
                f"<b>Срок:</b> {duration_labels.get(duration_key, duration_key)}\n"
                f"<b>Новая цена:</b> {new_price} ₽",
                parse_mode="HTML"
            )
            
            ADMIN_PRICE_STATE.pop(user_id, None)
        else:
            await message.answer(f"{emoji('5774077015388852135', '❌')} <b>Ошибка: тариф или срок не найден</b>", parse_mode="HTML")
            
    except ValueError:
        await message.answer(f"{emoji('5774077015388852135', '❌')} <b>Введите число</b>", parse_mode="HTML")
        return
    
    from handlers.start import bot
    await bot.edit_message_text(
        chat_id=state["chat_id"],
        message_id=state["msg_id"],
        text=f"{emoji('5904630315946611415', '👨‍💻')} <b>Админ панель</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )
    del admin_state[user_id]

@router.callback_query(F.data == "admin_servers")
async def admin_servers(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(ADMIN_SERVERS_EMOJI_ID, '🖥️')} <b>Управление серверами</b>",
        reply_markup=get_servers_management_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_servers_count")
async def admin_servers_count(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    servers = get_servers_from_file()
    if servers:
        text = f"{emoji(SERVERS_COUNT_EMOJI_ID, '📈')} <b>Список серверов:</b>\n\n" + "\n".join([f"{s['id']}. {s['name']}" for s in servers])
    else:
        text = f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Серверы не найдены</b>"
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard("admin_servers"), parse_mode="HTML")

@router.callback_query(F.data == "admin_server_add")
async def admin_server_add_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(ADD_EMOJI_ID, '➕')} <b>Отправьте ссылку на сервер (или несколько, каждую с новой строки):</b>\n\n"
        f"<i>Также можно отправить TXT файл со списком ссылок</i>",
        reply_markup=get_cancel_keyboard("admin_servers"),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "add_server", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_server_remove")
async def admin_server_remove_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    servers = get_servers_from_file()
    if not servers:
        await callback.answer("Нет серверов для удаления", show_alert=True)
        return
    text = f"{emoji(ADMIN_CROSS_EMOJI_ID, '🗑️')} <b>Выберите номер сервера для удаления:</b>\n\n" + "\n".join([f"{s['id']}. {s['name']}" for s in servers])
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard("admin_servers"), parse_mode="HTML")
    admin_state[callback.from_user.id] = {"action": "remove_server", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "admin_server_clear")
async def admin_server_clear_confirm(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Вы точно хотите очистить весь список серверов?</b>",
        reply_markup=get_confirm_keyboard("admin_server_clear_confirm", "admin_servers"),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_server_clear_confirm")
async def admin_server_clear_do(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    clear_servers_file()
    await callback.message.edit_text(
        f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Список серверов очищен</b>",
        reply_markup=get_admin_back_keyboard("admin_servers"),
        parse_mode="HTML"
    )

@router.message(F.text, lambda message: admin_state.get(message.from_user.id, {}).get("action") in ["ban", "unban", "give_subscription", "take_subscription", "add_server", "remove_server"])
async def handle_admin_text_input(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    state = admin_state.get(user_id, {})
    action = state.get("action")
    if not action:
        return

    if action == "ban":
        try:
            target_id = int(message.text.strip())
            if db.is_user_banned(target_id):
                await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Пользователь {target_id} уже забанен</b>", parse_mode="HTML")
            else:
                db.ban_user(target_id)
                await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Пользователь {target_id} забанен</b>", parse_mode="HTML")
        except ValueError:
            await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Неверный ID</b>", parse_mode="HTML")

    elif action == "unban":
        try:
            target_id = int(message.text.strip())
            if not db.is_user_banned(target_id):
                await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Пользователь {target_id} не забанен</b>", parse_mode="HTML")
            else:
                db.unban_user(target_id)
                await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Пользователь {target_id} разбанен</b>", parse_mode="HTML")
        except ValueError:
            await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Неверный ID</b>", parse_mode="HTML")

    elif action == "give_subscription":
        try:
            target_id = int(message.text.strip())
            plan = state.get("plan", "solo")
            
            if db.is_subscription_active(target_id):
                await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>У пользователя {target_id} уже активна подписка</b>", parse_mode="HTML")
            else:
                db.set_user_plan(target_id, plan)
                db.activate_premium(target_id, days=30)
                
                plan_names = {"solo": "Solo", "premium": "Premium", "family": "Family"}
                plan_name = plan_names.get(plan, plan.capitalize())
                
                await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Пользователю {target_id} выдана подписка {plan_name} на 30 дней</b>", parse_mode="HTML")
                from handlers.start import bot
                try:
                    plan_emojis = {
                        "solo": SOLO_EMOJI_ID,
                        "premium": PREMIUM_EMOJI_ID,
                        "family": FAMILY_EMOJI_ID
                    }
                    plan_emoji_id = plan_emojis.get(plan, SOLO_EMOJI_ID)
                    await bot.send_message(target_id, f"{emoji(GIVE_SUBSCRIPTION_EMOJI_ID, '👑')} <b>Администратор выдал вам подписку {plan_name} на 30 дней!</b>", parse_mode="HTML")
                except Exception:
                    pass
        except ValueError:
            await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Неверный ID</b>", parse_mode="HTML")

    elif action == "take_subscription":
        try:
            target_id = int(message.text.strip())
            if not db.is_subscription_active(target_id):
                await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>У пользователя {target_id} нет активной подписки</b>", parse_mode="HTML")
            else:
                db.disable_premium(target_id)
                await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>У пользователя {target_id} забрана подписка</b>", parse_mode="HTML")
                from handlers.start import bot
                try:
                    await bot.send_message(target_id, f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Администратор забрал у вас подписку</b>", parse_mode="HTML")
                except Exception:
                    pass
        except ValueError:
            await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Неверный ID</b>", parse_mode="HTML")

    elif action == "add_server":
        lines = message.text.strip().splitlines()
        added = 0
        for line in lines:
            line = line.strip()
            if line:
                add_server_to_file(line)
                added += 1
        await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Добавлено {added} серверов</b>", parse_mode="HTML")

    elif action == "remove_server":
        try:
            idx = int(message.text.strip())
            servers = get_servers_from_file()
            if 1 <= idx <= len(servers):
                remove_server_from_file(idx)
                await message.answer(f"{emoji(CHECK_EMOJI_NEW_ID, '✅')} <b>Сервер {idx} удалён</b>", parse_mode="HTML")
            else:
                await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Неверный номер сервера</b>", parse_mode="HTML")
        except ValueError:
            await message.answer(f"{emoji(ADMIN_CROSS_EMOJI_ID, '❌')} <b>Введите число</b>", parse_mode="HTML")

    from handlers.start import bot
    await bot.edit_message_text(
        chat_id=state["chat_id"],
        message_id=state["msg_id"],
        text=f"{emoji(MAN_EMOJI_ID, '👨‍💻')} <b>Админ панель</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )
    del admin_state[user_id]

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        f"{emoji(MAIL_EMOJI_ID, '📢')} <b>Выберите тип рассылки:</b>",
        reply_markup=get_broadcast_choice_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "broadcast_custom")
async def broadcast_custom_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    broadcast_type[callback.from_user.id] = "custom"
    await callback.message.edit_text(
        f"{emoji(MAIL_EMOJI_ID, '📢')} <b>Отправьте сообщение для рассылки (текст, фото, видео):</b>",
        reply_markup=get_cancel_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "broadcast_wait_message", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.callback_query(F.data == "broadcast_ready")
async def broadcast_ready_start(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    broadcast_type[callback.from_user.id] = "ready"
    await callback.message.edit_text(
        f"{emoji(MAIL_EMOJI_ID, '📋')} <b>Отправьте готовое сообщение для рассылки:</b>",
        reply_markup=get_cancel_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    admin_state[callback.from_user.id] = {"action": "broadcast_wait_ready_message", "msg_id": callback.message.message_id, "chat_id": callback.message.chat.id}

@router.message(F.chat.type == "private", lambda message: admin_state.get(message.from_user.id, {}).get("action") == "broadcast_wait_ready_message")
async def handle_ready_broadcast_message(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    msg_data = await parse_ready_message(message)
    if not msg_data:
        await message.answer("Неподдерживаемый тип сообщения")
        return
    pending_broadcast_buttons[user_id] = {"message_data": msg_data, "buttons": None, "type": "ready"}
    del admin_state[user_id]
    lang = "ru"
    await show_broadcast_preview(message, user_id, lang)

@router.message(F.chat.type == "private", lambda message: admin_state.get(message.from_user.id, {}).get("action") == "broadcast_wait_message")
async def handle_broadcast_message(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    lang = "ru"
    broadcast_data = {"type": "unknown"}
    if message.text:
        broadcast_data = {"type": "text", "text": message.text, "entities": message.entities}
    elif message.photo:
        broadcast_data = {"type": "photo", "photo": message.photo[-1].file_id, "caption": message.caption or "", "caption_entities": message.caption_entities}
    elif message.video:
        broadcast_data = {"type": "video", "video": message.video.file_id, "caption": message.caption or "", "caption_entities": message.caption_entities}
    else:
        await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Неподдерживаемый тип сообщения.</b>" if lang == "ru" else f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Unsupported message type.</b>", parse_mode="HTML")
        return
    pending_broadcast_buttons[user_id] = {"message_data": broadcast_data, "buttons": None, "type": "custom"}
    admin_state[user_id]["action"] = "broadcast_wait_buttons"
    text = (f"{emoji(PLUS_EMOJI_ID, '➕')} <b>Добавление кнопок</b>\n\n"
            f"• <i>Новая строка = новая кнопка\n"
            f"• Несколько кнопок в ряд — раздели через |\n"
            f"• Цвет в конце: зелёный, синий или красный</i>\n\n"
            f"<b>Шаблон сообщения:</b>\n"
            f"<blockquote expandable>{emoji(THUMBS_UP_EMOJI_ID, '👍')} Лучший VPN — https://t.me/StreamNetVPN_bot — зелёный\n"
            f"Поддержка — https://t.me/StreamNetAdmin | Наш сайт — https://streamnetvpn.top — синий</blockquote>\n\n"
            f"{emoji(CLICK_DOWN_NEW_EMOJI_ID, '👇')} <b>Отправь кнопки:</b>\n")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"Пропустить" if lang == "ru" else f"Skip", callback_data="skip_buttons", style="primary", icon_custom_emoji_id=FAST_FORWARD_EMOJI_ID))
    kb.row(InlineKeyboardButton(text=f"Отмена" if lang == "ru" else f"Cancel", callback_data="cancel_broadcast", style="danger", icon_custom_emoji_id=CANCEL_EMOJI_ID))
    await message.answer(text, reply_markup=kb.as_markup(), link_preview_options=LinkPreviewOptions(is_disabled=True), parse_mode="HTML")

@router.message(F.text, lambda message: admin_state.get(message.from_user.id, {}).get("action") == "broadcast_wait_buttons")
async def handle_buttons_input(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    lang = "ru"
    keyboard = await parse_buttons_from_text(message, lang)
    if keyboard is None:
        await message.answer(f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Ошибка в формате кнопок. Попробуйте снова или нажмите «Пропустить».</b>" if lang == "ru" else f"{emoji(WARNING_EMOJI_ID, '⚠️')} <b>Invalid button format. Try again or press «Skip».</b>", link_preview_options=LinkPreviewOptions(is_disabled=True), parse_mode="HTML")
        return
    pending_broadcast_buttons[user_id]["buttons"] = keyboard
    del admin_state[user_id]
    await show_broadcast_preview(message, user_id, lang)

@router.callback_query(F.data == "skip_buttons")
async def skip_buttons(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer()
        return
    lang = "ru"
    pending_broadcast_buttons[user_id]["buttons"] = None
    del admin_state[user_id]
    await show_broadcast_preview(callback.message, user_id, lang)
    await callback.answer()

@router.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    lang = "ru"
    data = pending_broadcast_buttons.get(user_id, {})
    msg_data = data.get("message_data")
    keyboard = data.get("buttons")
    b_type = data.get("type", "custom")
    if not msg_data:
        await callback.answer("No data for broadcast", show_alert=True)
        return
    users = db.get_all_users()
    await callback.message.edit_text(f"{emoji(BROADCAST_START_EMOJI_ID, '📢')} <b>Рассылка начата...</b>" if lang == "en" else f"{emoji(BROADCAST_START_EMOJI_ID, '📢')} <b>Рассылка начата...</b>", parse_mode="HTML")
    success = 0
    for user in users:
        try:
            if b_type == "ready":
                await send_ready_broadcast_message(user, msg_data)
            else:
                if msg_data["type"] == "text":
                    if msg_data.get("entities"):
                        class FakeMessage:
                            def __init__(self, text, entities):
                                self.text = text
                                self.entities = entities
                        fake_msg = FakeMessage(msg_data["text"], msg_data["entities"])
                        html_text = await convert_message_to_html(fake_msg)
                        await send_safe_message(user, html_text, keyboard)
                    else:
                        await send_safe_message(user, msg_data["text"], keyboard)
                elif msg_data["type"] == "photo":
                    caption = msg_data.get("caption", "")
                    if msg_data.get("caption_entities"):
                        class FakeMessage:
                            def __init__(self, text, entities):
                                self.text = text
                                self.entities = entities
                        fake_msg = FakeMessage(caption, msg_data["caption_entities"])
                        caption = await convert_message_to_html(fake_msg)
                        await send_safe_photo(user, msg_data["photo"], caption, keyboard)
                elif msg_data["type"] == "video":
                    caption = msg_data.get("caption", "")
                    if msg_data.get("caption_entities"):
                        class FakeMessage:
                            def __init__(self, text, entities):
                                self.text = text
                                self.entities = entities
                        fake_msg = FakeMessage(caption, msg_data["caption_entities"])
                        caption = await convert_message_to_html(fake_msg)
                        await send_safe_video(user, msg_data["video"], caption, keyboard)
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Broadcast error to {user}: {e}")
    del pending_broadcast_buttons[user_id]
    broadcast_type.pop(user_id, None)
    await callback.message.edit_text(f"{emoji(CHECK_MARK_EMOJI_ID, '✅')} <b>Рассылка завершена!</b>\n\n<i>Отправлено: {success} / {len(users)} пользователям</i>.", reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await callback.answer()
    pending_broadcast_buttons.pop(callback.from_user.id, None)
    broadcast_type.pop(callback.from_user.id, None)
    if callback.from_user.id in admin_state:
        del admin_state[callback.from_user.id]
    lang = "ru"
    await callback.message.edit_text(
        f"{emoji(MAN_EMOJI_ID, '👨‍💻')} <b>Админ панель</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )