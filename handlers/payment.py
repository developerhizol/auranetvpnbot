# handlers/payment.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from utils.platega import platega, PAYMENT_METHODS
import logging

router = Router()
user_payment = {}
user_transactions = {}

logger = logging.getLogger(__name__)

SUBSCRIPTION_DOMAIN = "streamnetvpn.bothost.tech"

PLANS = {
    "solo": {
        "name": "Solo",
        "devices": "2",
        "devices_text": "2-х",
        "price_month": 99,
        "price_3months": 249,
        "price_6months": 549,
        "emoji_id": "5258011929993026890",
        "fallback": "👤",
        "days_month": 30,
        "days_3months": 90,
        "days_6months": 180
    },
    "premium": {
        "name": "Premium",
        "devices": "5",
        "devices_text": "5-ти",
        "price_month": 149,
        "price_3months": 399,
        "price_6months": 829,
        "emoji_id": "5258513401784573443",
        "fallback": "👥",
        "days_month": 30,
        "days_3months": 90,
        "days_6months": 180
    },
    "family": {
        "name": "Family",
        "devices": "8",
        "devices_text": "8-ми",
        "price_month": 199,
        "price_3months": 549,
        "price_6months": 1149,
        "emoji_id": "5257963315258204021",
        "fallback": "🏠",
        "days_month": 30,
        "days_3months": 90,
        "days_6months": 180
    }
}

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

@router.callback_query(F.data == "pay_subscription")
async def pay_subscription(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id in user_payment:
        del user_payment[user_id]
    
    text = (
        f"<b>Выберите удобный вам тариф:</b>\n\n"
        f"{emoji('5258011929993026890', '👤')} <b>Solo</b> — 2 устр.\n"
        f"{emoji('5258513401784573443', '👥')} <b>Premium</b> — 5 устр.\n"
        f"{emoji('5257963315258204021', '🏠')} <b>Family</b> — 8 устр.\n\n"
        f"{emoji('5323761960829862762', '⚡')} <b>Выберите тариф:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Solo – от 99₽ • для себя",
            callback_data="plan_solo",
            icon_custom_emoji_id="5258011929993026890"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Premium - от 149₽ • оптимальный",
            callback_data="plan_premium",
            style="primary",
            icon_custom_emoji_id="5258513401784573443"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Family - от 199₽ • семейный",
            callback_data="plan_family",
            icon_custom_emoji_id="5257963315258204021"
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

@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    plan_key = callback.data.split("_")[1]
    
    if plan_key not in PLANS:
        await callback.answer("Тариф не найден", show_alert=True)
        return
    
    plan = PLANS[plan_key]
    user_payment[user_id] = {"plan": plan_key}
    
    text = (
        f"{emoji(plan['emoji_id'], plan['fallback'])} <b>Тариф: {plan['name']}</b>\n"
        f"├ До {plan['devices_text']} устройств\n"
        f"╰ Безлимит трафика\n\n"
        f"{emoji('5323761960829862762', '⚡')} <b>Выберите срок:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"1 мес. — {plan['price_month']}₽",
            callback_data=f"duration_{plan_key}_month"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"3 мес. — {plan['price_3months']}₽",
            callback_data=f"duration_{plan_key}_3months"
        ),
        InlineKeyboardButton(
            text=f"6 мес. — {plan['price_6months']}₽",
            callback_data=f"duration_{plan_key}_6months"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="pay_subscription"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("duration_"))
async def select_duration(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    plan_key = parts[1]
    duration_key = parts[2]
    
    if user_id not in user_payment:
        await callback.answer("Ошибка, попробуйте сначала", show_alert=True)
        return
    
    plan = PLANS[plan_key]
    
    duration_labels = {
        "month": "1 мес.",
        "3months": "3 мес.",
        "6months": "6 мес."
    }
    
    duration_prices = {
        "month": plan["price_month"],
        "3months": plan["price_3months"],
        "6months": plan["price_6months"]
    }
    
    duration_days = {
        "month": plan["days_month"],
        "3months": plan["days_3months"],
        "6months": plan["days_6months"]
    }
    
    label = duration_labels.get(duration_key, "1 мес.")
    price = duration_prices.get(duration_key, plan["price_month"])
    days = duration_days.get(duration_key, 30)
    
    user_payment[user_id].update({
        "duration": duration_key,
        "duration_label": label,
        "price": price,
        "days": days
    })
    
    await show_payment_methods(callback.message, user_id, plan_key, duration_key)

async def show_payment_methods(message, user_id: int, plan_key: str, duration_key: str):
    plan = PLANS[plan_key]
    
    duration_labels = {
        "month": "1 мес.",
        "3months": "3 мес.",
        "6months": "6 мес."
    }
    
    duration_prices = {
        "month": plan["price_month"],
        "3months": plan["price_3months"],
        "6months": plan["price_6months"]
    }
    
    label = duration_labels.get(duration_key, "1 мес.")
    price = duration_prices.get(duration_key, plan["price_month"])
    
    privacy_url = "https://telegra.ph/Politika-konfidencialnosti-04-01-26"
    terms_url = "https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19"
    
    text = (
        f"{emoji('5444903695256941915', '💲')} <b>Способ оплаты:</b> <code>...</code>\n"
        f"{emoji('5444860552310457690', '💸')} <b>Стоимость:</b> <code>{price} ₽</code>\n"
        f"{emoji('5258258882022612173', '🕛')} <b>Срок:</b> <code>{label}</code>\n\n"
        f"<i>Нажимая «Оплатить» вы подтверждаете что ознакомились и полностью согласны с "
        f'<a href="{privacy_url}">политикой конфиденциальности</a> и '
        f'<a href="{terms_url}">пользовательским соглашением</a>.</i>'
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="СБП",
            callback_data=f"pay_method_sbp_{plan_key}_{duration_key}",
            icon_custom_emoji_id="5425008221330880308"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Банковская карта",
            callback_data=f"pay_method_card_{plan_key}_{duration_key}",
            icon_custom_emoji_id="5447453226498552490"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Криптовалюта",
            callback_data=f"pay_method_crypto_{plan_key}_{duration_key}",
            icon_custom_emoji_id="5447579253723918909"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"plan_{plan_key}"
        )
    )
    
    await message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def show_payment_confirmation(message, user_id: int, method_key: str, plan_key: str, duration_key: str, redirect_url: str = None):
    plan = PLANS[plan_key]
    
    duration_labels = {
        "month": "1 мес.",
        "3months": "3 мес.",
        "6months": "6 мес."
    }
    
    duration_prices = {
        "month": plan["price_month"],
        "3months": plan["price_3months"],
        "6months": plan["price_6months"]
    }
    
    method = PAYMENT_METHODS[method_key]
    label = duration_labels.get(duration_key, "1 мес.")
    price = duration_prices.get(duration_key, plan["price_month"])
    
    privacy_url = "https://telegra.ph/Politika-konfidencialnosti-04-01-26"
    terms_url = "https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19"
    
    text = (
        f"{emoji('5444903695256941915', '💲')} <b>Способ оплаты:</b> <code>{method['name']}</code>\n"
        f"{emoji('5444860552310457690', '💸')} <b>Стоимость:</b> <code>{price} ₽</code>\n"
        f"{emoji('5258258882022612173', '🕛')} <b>Срок:</b> <code>{label}</code>\n\n"
        f"<i>Нажимая «Оплатить» вы подтверждаете что ознакомились и полностью согласны с "
        f'<a href="{privacy_url}">политикой конфиденциальности</a> и '
        f'<a href="{terms_url}">пользовательским соглашением</a>.</i>'
    )
    
    builder = InlineKeyboardBuilder()
    
    if redirect_url:
        builder.row(
            InlineKeyboardButton(
                text="Оплатить",
                url=redirect_url,
                style="primary",
                icon_custom_emoji_id="5444903695256941915"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Оплатить",
                callback_data=f"pay_create_{method_key}_{plan_key}_{duration_key}",
                style="primary",
                icon_custom_emoji_id="5444903695256941915"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="Проверить оплату",
            callback_data=f"pay_check_{method_key}_{plan_key}_{duration_key}",
            style="success",
            icon_custom_emoji_id="5444860552310457690"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="pay_cancel",
            style="danger",
            icon_custom_emoji_id="5258258882022612173"
        )
    )
    
    await message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.callback_query(F.data.startswith("pay_method_"))
async def select_payment_method(callback: CallbackQuery):
    parts = callback.data.split("_")
    method_key = parts[2]
    plan_key = parts[3]
    duration_key = parts[4]
    
    user_id = callback.from_user.id
    
    if method_key == "crypto":
        await callback.answer(
            "⏳ Оплата криптовалютой в разработке...",
            show_alert=True
        )
        return
    
    user_payment[user_id]["method"] = method_key
    
    await create_payment_and_show(callback.message, user_id, method_key, plan_key, duration_key)
    await callback.answer()

@router.callback_query(F.data.startswith("pay_create_"))
async def create_payment(callback: CallbackQuery):
    parts = callback.data.split("_")
    method_key = parts[2]
    plan_key = parts[3]
    duration_key = parts[4]
    
    user_id = callback.from_user.id
    
    await create_payment_and_show(callback.message, user_id, method_key, plan_key, duration_key)
    await callback.answer()

async def create_payment_and_show(message, user_id: int, method_key: str, plan_key: str, duration_key: str):
    if user_id not in user_payment:
        await message.answer("Ошибка, попробуйте сначала")
        return
    
    plan = PLANS[plan_key]
    duration_prices = {
        "month": plan["price_month"],
        "3months": plan["price_3months"],
        "6months": plan["price_6months"]
    }
    price = duration_prices.get(duration_key, plan["price_month"])
    
    method = PAYMENT_METHODS[method_key]
    
    description = f"Оплата подписки {plan['name']} {duration_key}"
    payload = f"{user_id}:{plan_key}:{duration_key}"
    return_url = f"https://t.me/StreamNetVPN_bot"
    failed_url = f"https://t.me/StreamNetVPN_bot"
    
    user = db.get_user(user_id)
    username = user.get("username") if user else None
    
    transaction = await platega.create_transaction(
        user_id=user_id,
        amount=price,
        payment_method=method["id"],
        description=description,
        return_url=return_url,
        failed_url=failed_url,
        payload=payload,
        username=username
    )
    
    if not transaction:
        await message.answer(
            "❌ Ошибка создания платежа. Попробуйте позже."
        )
        return
    
    user_transactions[user_id] = transaction.get("transactionId")
    redirect_url = transaction.get("redirect")
    
    await show_payment_confirmation(
        message,
        user_id,
        method_key,
        plan_key,
        duration_key,
        redirect_url
    )

@router.callback_query(F.data.startswith("pay_check_"))
async def check_payment(callback: CallbackQuery):
    parts = callback.data.split("_")
    method_key = parts[2]
    plan_key = parts[3]
    duration_key = parts[4]
    
    user_id = callback.from_user.id
    
    if user_id not in user_transactions:
        await callback.answer(
            "⏳ Платёж ещё не создан. Нажмите «Оплатить» сначала.",
            show_alert=True
        )
        return
    
    transaction_id = user_transactions[user_id]
    
    result = await platega.check_transaction(transaction_id)
    
    if not result:
        await callback.answer(
            "❌ Ошибка проверки платежа. Попробуйте позже.",
            show_alert=True
        )
        return
    
    status = result.get("status")
    
    if status == "CONFIRMED":
        await callback.answer(
            "✅ Оплата подтверждена. Спасибо за покупку :)",
            show_alert=True
        )
        
        plan = PLANS[plan_key]
        days = {
            "month": plan["days_month"],
            "3months": plan["days_3months"],
            "6months": plan["days_6months"]
        }.get(duration_key, 30)
        
        db.set_user_plan(user_id, plan_key)
        db.activate_premium(user_id, days=days)
        
        price = {
            "month": plan["price_month"],
            "3months": plan["price_3months"],
            "6months": plan["price_6months"]
        }.get(duration_key, plan["price_month"])
        db.log_payment(user_id, price)
        db.log_premium_purchase(user_id, price)
        
        user_payment.pop(user_id, None)
        user_transactions.pop(user_id, None)
        
        from handlers.start import edit_main_menu
        first_name = callback.from_user.first_name
        username = callback.from_user.username
        
        await edit_main_menu(callback, user_id, first_name, username)
        
    elif status == "PENDING":
        await callback.answer(
            "⏳ Оплата ещё не поступила. Попробуйте позже...",
            show_alert=True
        )

@router.callback_query(F.data == "pay_cancel")
async def cancel_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_payment.pop(user_id, None)
    user_transactions.pop(user_id, None)
    
    await callback.answer("❌ Оплата отменена")
    
    await pay_subscription(callback)