from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db

router = Router()

CONFIG_URL = "https://subscription.bothost.tech/sub/"

def get_device_keyboard(config_link: str):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Скачать приложение", url="https://t.me/Happ_proxy_bot?start=download")
    builder.button(text="🔗 Подключиться", url=config_link, style="success")
    builder.button(text="« Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data == "connect_vpn")
async def connect_vpn(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_active = db.is_subscription_active(user_id)
    
    if is_active:
        token = str(user_id)
        config_link = f"{CONFIG_URL}{token}"
        text = (
            f"🔐 <b>Ваш VPN готов к подключению</b>\n\n"
            f"1. Скачайте приложение Happ\n"
            f"2. Нажмите «Подключиться»\n"
            f"3. Готово!\n\n"
            f"<i>Если не подключается — обновите подписку в приложении</i>"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_device_keyboard(config_link),
            parse_mode="HTML"
        )
    else:
        from keyboards.main_menu import get_main_keyboard
        text = (
            f"❌ <b>Ваша подписка истекла</b>\n\n"
            f"Пожалуйста, оплатите подписку, чтобы продолжить пользоваться VPN."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()