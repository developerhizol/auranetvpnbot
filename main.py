# main.py - ПОЛНЫЙ ФАЙЛ
import asyncio
import logging
import secrets
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN
from database import db
from handlers import start_router, about_service_router, help_router, admin_router, payment_router, profile_router
from utils.admin_utils import get_servers_from_file

logging.basicConfig(level=logging.INFO)

PORT = 9283
SUBSCRIPTION_DOMAIN = "streamnetvpn.bothost.tech"

BAN_EMOJI_ID = "5258318620722733379"

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

BAN_EMOJI = emoji(BAN_EMOJI_ID, "🚫")

def generate_token() -> str:
    return secrets.token_urlsafe(9)[:12]

def get_or_create_user_token(user_id: int) -> str:
    token = db.get_user_token(user_id)
    if not token:
        token = generate_token()
        db.save_user_token(user_id, token)
    return token

def get_device_identifier(user_agent: str, ip: str, headers: dict = None) -> str:
    ua = user_agent or ''
    
    if headers:
        hwid = headers.get('X-Hwid') or headers.get('X-HWID') or headers.get('X-Device-Id')
        if hwid:
            logging.info(f"✅ Использую HWID: {hwid}")
            return hwid
    
    model = parse_device_model(ua)
    if model:
        return f"{model}_{ip}"
    
    return f"{ua}|{ip}"

def parse_device_model(user_agent: str) -> str:
    if not user_agent:
        return None
    
    ua = user_agent
    
    pattern = r'\(([A-Za-z0-9\s\-_]+);\s*Android'
    match = re.search(pattern, ua)
    if match:
        model = match.group(1).strip()
        model = re.sub(r'\s+', ' ', model)
        if model and len(model) > 2 and model not in ['K', 'L', 'M', 'N']:
            return model
    
    pattern2 = r'Android\s+[\d.]+\s*;\s*([A-Za-z0-9\s\-_]+?)(?:[;)])'
    match = re.search(pattern2, ua)
    if match:
        model = match.group(1).strip()
        model = re.sub(r'\s+', ' ', model)
        if model and len(model) > 2 and model not in ['K', 'L', 'M', 'N']:
            return model
    
    return None

def pluralize_devices(count: int) -> str:
    if 11 <= count % 100 <= 19:
        return f"{count} устройств"
    elif count % 10 == 1:
        return f"{count} устройство"
    elif 2 <= count % 10 <= 4:
        return f"{count} устройства"
    else:
        return f"{count} устройств"

def get_device_display_name(user_agent: str, headers: dict = None) -> str:
    if headers:
        model = headers.get('X-Device-Model')
        if model:
            return model
    
    model = parse_device_model(user_agent)
    if model:
        return model
    
    return "Неизвестное устройство"

def get_days_until_expiry(subscription_end) -> int:
    if not subscription_end:
        return 0
    
    if isinstance(subscription_end, str):
        subscription_end = datetime.fromisoformat(subscription_end)
    
    now = datetime.now()
    delta = subscription_end - now
    days = delta.days
    
    if days == 0 and delta.total_seconds() > 0:
        return 1
    
    return max(0, days)

def get_hours_until_expiry(subscription_end) -> int:
    if not subscription_end:
        return 0
    
    if isinstance(subscription_end, str):
        subscription_end = datetime.fromisoformat(subscription_end)
    
    now = datetime.now()
    delta = subscription_end - now
    return max(0, int(delta.total_seconds() / 3600))

def get_profile_headers_dynamic(user_id: int) -> list:
    headers = ["#profile-title: 🚀 stream net"]
    
    is_banned = db.is_user_banned(user_id)
    is_active = db.is_subscription_active(user_id)
    
    if is_banned or not is_active:
        headers.append("#profile-update-interval: 1")
        headers.append("")
        return headers
    
    subscription_end = db.get_subscription_end(user_id)
    if not subscription_end:
        headers.append("#profile-update-interval: 1")
        headers.append("")
        return headers
    
    if isinstance(subscription_end, str):
        subscription_end = datetime.fromisoformat(subscription_end)
    
    hours_left = get_hours_until_expiry(subscription_end)
    days_left = get_days_until_expiry(subscription_end)
    
    if hours_left < 24:
        headers.append("#announce: ⏳ Подписка истекает сегодня")
    elif days_left == 1:
        headers.append("#announce: ⏳ Подписка истекает через 1 день")
    elif 2 <= days_left <= 4:
        headers.append(f"#announce: ⏳ Подписка истекает через {days_left} дня")
    else:
        headers.append(f"#announce: ⏳ Подписка истекает через {days_left} дней")
    
    headers.append("#profile-update-interval: 1")
    headers.append("")
    
    return headers

async def check_subscriptions(bot: Bot):
    while True:
        try:
            users = db.get_all_users()
            now = datetime.now()
            
            for user_id in users:
                try:
                    user = db.get_user(user_id)
                    if not user:
                        continue
                    
                    is_active = db.is_subscription_active(user_id)
                    sub_info = db.get_subscription_info(user_id)
                    
                    if not sub_info:
                        continue
                    
                    subscription_end = sub_info.get('subscription_end')
                    if not subscription_end:
                        continue
                    
                    if not is_active:
                        if sub_info.get('notify_expired_sent') == 0:
                            text = f"{emoji('5447621159719827951', '🔔')} <b>Ваша подписка истекла!</b>\n\n{emoji('5444903695256941915', '💳')} <i>Оплатите подписку чтобы восстановить доступ к серверам</i>"
                            builder = InlineKeyboardBuilder()
                            builder.row(
                                InlineKeyboardButton(
                                    text="Оплатить подписку",
                                    callback_data="pay_subscription",
                                    style="primary",
                                    icon_custom_emoji_id="5258258882022612173"
                                )
                            )
                            try:
                                await bot.send_message(user_id, text, reply_markup=builder.as_markup(), parse_mode="HTML")
                                db.set_notify_expired_sent(user_id, 1)
                                logging.info(f"Уведомление об истечении отправлено пользователю {user_id}")
                            except Exception as e:
                                logging.error(f"Ошибка отправки уведомления об истечении {user_id}: {e}")
                        continue
                    
                    if isinstance(subscription_end, str):
                        subscription_end = datetime.fromisoformat(subscription_end)
                    
                    time_left = subscription_end - now
                    hours_left = time_left.total_seconds() / 3600
                    
                    if hours_left <= 24 and sub_info.get('notify_24h_sent') == 0:
                        text = f"{emoji('5447621159719827951', '🔔')} <b>До конца вашей подписки осталось менее 24 часов</b>\n\n{emoji('5444903695256941915', '💳')} <i>Оплатите подписку чтобы не потерять доступ к серверам</i>"
                        builder = InlineKeyboardBuilder()
                        builder.row(
                            InlineKeyboardButton(
                                text="Оплатить подписку",
                                callback_data="pay_subscription",
                                style="primary",
                                icon_custom_emoji_id="5258258882022612173"
                            )
                        )
                        try:
                            await bot.send_message(user_id, text, reply_markup=builder.as_markup(), parse_mode="HTML")
                            db.set_notify_24h_sent(user_id, 1)
                            logging.info(f"Уведомление за 24 часа отправлено пользователю {user_id}")
                        except Exception as e:
                            logging.error(f"Ошибка отправки уведомления за 24 часа {user_id}: {e}")
                    
                    elif hours_left > 24 and sub_info.get('notify_24h_sent') == 1:
                        db.set_notify_24h_sent(user_id, 0)
                        
                except Exception as e:
                    logging.error(f"Ошибка проверки подписки пользователя {user_id}: {e}")
                    continue
            
            await asyncio.sleep(3600)
            
        except Exception as e:
            logging.error(f"Ошибка в check_subscriptions: {e}")
            await asyncio.sleep(3600)

async def handle_token_info(request):
    token = request.match_info.get('token')
    conn = db._get_connection()
    row = conn.execute("SELECT user_id FROM user_tokens WHERE token = ?", (token,)).fetchone()
    conn.close()
    if not row:
        return web.json_response({"error": "Token not found"}, status=404)
    user_id = row['user_id']
    user = db.get_user(user_id)
    if not user:
        return web.json_response({"error": "User not found"}, status=404)
    is_active = db.is_subscription_active(user_id)
    subscription_end = db.get_subscription_end(user_id)
    plan = db.get_user_plan(user_id)
    device_limit = db.get_device_limit(user_id)
    active_devices = db.get_active_devices_count(user_id)
    
    response_data = {
        "status": "active" if is_active else "inactive",
        "first_name": user.get('first_name', 'User'),
        "username": user.get('username', ''),
        "user_id": user_id,
        "expires_at": subscription_end.isoformat() if subscription_end else None,
        "plan": plan,
        "device_limit": device_limit,
        "active_devices": active_devices
    }
    return web.json_response(response_data)

def is_browser(user_agent: str) -> bool:
    if not user_agent:
        return True
    user_agent_lower = user_agent.lower()
    browser_keywords = [
        'mozilla', 'chrome', 'safari', 'firefox', 'opera', 'edge', 
        'brave', 'vivaldi', 'yandex', 'trident', 'msie', 'webview',
        'android', 'iphone', 'ipad', 'macintosh', 'windows', 'linux'
    ]
    app_keywords = [
        'happ', 'nekobox', 'v2ray', 'clash', 'sing-box', 'shadowrocket',
        'stash', 'surge', 'quantumult', 'kitsunebi', 'postman', 'curl', 'wget',
        'v2raytun'
    ]
    
    for keyword in app_keywords:
        if keyword in user_agent_lower:
            return False
    for keyword in browser_keywords:
        if keyword in user_agent_lower:
            return True
    return True

def is_happ(user_agent: str) -> bool:
    if not user_agent:
        return False
    return 'happ' in user_agent.lower()

def is_bot(user_agent: str) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    bot_keywords = ['telegrambot', 'twitterbot', 'bot/', 'spider', 'crawler']
    for keyword in bot_keywords:
        if keyword in ua:
            return True
    return False

def get_config_for_user(user_id: int, device_id: str = None, device_name: str = None, token: str = None) -> str:
    is_banned = db.is_user_banned(user_id)
    is_active = db.is_subscription_active(user_id)
    
    if is_banned:
        headers = ["#profile-title: 🚀 stream net", "#profile-update-interval: 1", ""]
        config_lines = headers.copy()
        config_lines.append("vless://#🚫 Аккаунт заблокирован")
        return "\n".join(config_lines)
    
    if not is_active:
        headers = ["#profile-title: 🚀 stream net", "#profile-update-interval: 1", ""]
        config_lines = headers.copy()
        config_lines.append("vless://#⚠️ Подписка истекла")
        config_lines.append("vless://#Продлить - @streamnetvpnbot")
        return "\n".join(config_lines)
    
    headers = get_profile_headers_dynamic(user_id)
    config_lines = headers.copy()
    
    current_token = db.get_user_token(user_id)
    if token and token != current_token:
        config_lines.append("vless://#❌ Ключ неактивен")
        return "\n".join(config_lines)
    
    if device_id:
        if not db.device_exists(user_id, device_id):
            if db.is_device_limit_exceeded(user_id):
                limit = db.get_device_limit(user_id)
                config_lines.append("vless://#⚠️ Превышен лимит устройств")
                config_lines.append(f"vless://#Лимит: {pluralize_devices(limit)}")
                return "\n".join(config_lines)
            db.register_device_fingerprint(user_id, device_id, device_name)
        else:
            conn = db._get_connection()
            conn.execute(
                "UPDATE device_fingerprints SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ? AND fingerprint = ?",
                (user_id, device_id)
            )
            conn.commit()
            conn.close()
    
    servers = get_servers_from_file()
    if servers:
        for server in servers:
            config_lines.append(server["full"])
    else:
        config_lines.append("# Серверы не найдены. Добавьте серверы в админ-панели.")
    
    return "\n".join(config_lines)

async def serve_index():
    index_path = Path(__file__).parent / 'public' / 'index.html'
    if not index_path.exists():
        return web.Response(text="index.html not found", status=404)
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return web.Response(text=html, content_type='text/html')

async def handle_sub(request):
    token = request.match_info.get('token', '')
    
    if not token:
        return web.json_response({"error": "Access denied"}, status=403)
    
    user_agent = request.headers.get('User-Agent', '')
    client_ip = request.headers.get('X-Forwarded-For', request.remote)
    
    headers_dict = {}
    for key, value in request.headers.items():
        headers_dict[key] = value
    
    logging.info(f"User-Agent: {user_agent}")
    
    hwid = headers_dict.get('X-Hwid') or headers_dict.get('X-HWID') or headers_dict.get('X-Device-Id')
    model = headers_dict.get('X-Device-Model')
    if hwid:
        logging.info(f"🔑 HWID: {hwid}")
    if model:
        logging.info(f"📱 Model: {model}")
    
    conn = db._get_connection()
    row = conn.execute("SELECT user_id FROM user_tokens WHERE token = ?", (token,)).fetchone()
    conn.close()
    
    if not row:
        if is_browser(user_agent):
            return await serve_index()
        return web.Response(text="Invalid token", status=403)
    
    user_id = row['user_id']
    
    if is_bot(user_agent):
        logging.info(f"🤖 Обнаружен бот, пропускаем без регистрации")
        config_text = get_config_for_user(user_id, None, None, token)
        return web.Response(text=config_text, content_type='text/plain')
    
    if is_browser(user_agent):
        return await serve_index()
    
    if not is_happ(user_agent):
        logging.info(f"❌ Запрос не от Happ, возвращаем ошибку")
        return web.Response(text="Ошибка: подписка доступна только в приложении Happ", status=403)
    
    device_id = get_device_identifier(user_agent, client_ip, headers_dict)
    device_name = get_device_display_name(user_agent, headers_dict)
    
    logging.info(f"🔑 Device ID: {device_id}, Device Name: {device_name}")
    
    if not db.device_exists(user_id, device_id):
        if db.is_device_limit_exceeded(user_id):
            config_text = get_config_for_user(user_id, device_id, device_name, token)
            return web.Response(text=config_text, content_type='text/plain')
        db.register_device_fingerprint(user_id, device_id, device_name)
    else:
        conn = db._get_connection()
        conn.execute(
            "UPDATE device_fingerprints SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ? AND fingerprint = ?",
            (user_id, device_id)
        )
        conn.commit()
        conn.close()
    
    config_text = get_config_for_user(user_id, device_id, device_name, token)
    return web.Response(text=config_text, content_type='text/plain')

async def start_webapp():
    app = web.Application()
    app.router.add_get('/api/token/{token}', handle_token_info)
    app.router.add_get('/sub/{token}', handle_sub)
    app.router.add_get('/', handle_sub)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Сервер Mini App и API запущен на порту {PORT}")

async def get_banned_message() -> str:
    return f"{BAN_EMOJI} <b>Вы были заблокированы.</b>\n\nЕсли считаете, что ваш бан был необоснованным, свяжитесь с администрацией."

async def get_banned_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Связаться с админом",
            url="https://t.me/StreamNetAdmin",
            style="primary"
        )
    )
    return builder

from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], 
        event: types.Message, 
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, (types.Message, types.CallbackQuery)):
            user_id = event.from_user.id
            if db.is_user_banned(user_id) and user_id != 7752488661:
                text = await get_banned_message()
                builder = await get_banned_keyboard()
                
                if isinstance(event, types.Message):
                    await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                elif isinstance(event, types.CallbackQuery):
                    await event.answer("🚫 Вы заблокированы", show_alert=True)
                    try:
                        await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                    except Exception:
                        pass
                return
        return await handler(event, data)

def main():
    db._init_db()
    logging.info("База данных инициализирована")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_all():
        await start_webapp()
        
        bot = Bot(token=BOT_TOKEN)
        
        asyncio.create_task(check_subscriptions(bot))
        logging.info("Планировщик уведомлений запущен")
        
        from handlers.start import bot as start_bot
        start_bot = bot
        
        dp = Dispatcher()
        dp.message.middleware(BanMiddleware())
        dp.callback_query.middleware(BanMiddleware())
        
        dp.include_router(start_router)
        dp.include_router(about_service_router)
        dp.include_router(help_router)
        dp.include_router(admin_router)
        dp.include_router(payment_router)
        dp.include_router(profile_router)
        
        logging.info("Бот запущен")
        await dp.start_polling(bot)
    
    try:
        loop.run_until_complete(run_all())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
    finally:
        loop.close()

if __name__ == "__main__":
    main()