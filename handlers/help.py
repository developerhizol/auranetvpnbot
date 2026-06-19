from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.help_keyboard import get_help_keyboard

router = Router()

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    warning_emoji = emoji("6019289243916968110", "📡")
    satellite_emoji = emoji("5931472654660800739", "📶")
    
    text = (
        f"{warning_emoji} <b>VPN:</b>\n"
        f"1. Обновите подписку в приложении Happ\n"
        f"2. Если не помогло — получите актуальный конфиг\n\n"
        f"{satellite_emoji} <b>Прокси:</b>\n"
        f"Переключитесь с мобильной сети на Wi-Fi и наоборот"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()