from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

ADMIN_MAIL_EMOJI_ID = "5771695636411847302"
ADMIN_STATS_EMOJI_ID = "5936143551854285132"
ADMIN_UNBAN_EMOJI_ID = "5774022692642492953"
ADMIN_BAN_EMOJI_ID = "5774077015388852135"
ADMIN_PRICE_EMOJI_ID = "5974217466270716579"
ADMIN_SERVERS_EMOJI_ID = "5291980250811506652"
GIVE_SUBSCRIPTION_EMOJI_ID = "6023940002008799618"
TAKE_SUBSCRIPTION_EMOJI_ID = "6021852682262682598"
SERVERS_COUNT_EMOJI_ID = "5938539885907415367"
ADMIN_CROSS_EMOJI_ID = "5774077015388852135"
PLUS_EMOJI_ID = "5775937998948404844"
SERVERS_CLEAR_EMOJI_ID = "5774077015388852135"
CANCEL_EMOJI_ID = "5774077015388852135"
CHECK_EMOJI_NEW_ID = "5774022692642492953"
SOLO_EMOJI_ID = "5258011929993026890"
PREMIUM_EMOJI_ID = "5258513401784573443"
FAMILY_EMOJI_ID = "5257963315258204021"

def get_admin_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Рассылка",
            callback_data="admin_broadcast",
            style="primary",
            icon_custom_emoji_id=ADMIN_MAIL_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Статистика",
            callback_data="admin_stats",
            style="primary",
            icon_custom_emoji_id=ADMIN_STATS_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Разбан",
            callback_data="admin_unban",
            style="success",
            icon_custom_emoji_id=ADMIN_UNBAN_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Бан",
            callback_data="admin_ban",
            style="danger",
            icon_custom_emoji_id=ADMIN_BAN_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Цена",
            callback_data="admin_price",
            style="primary",
            icon_custom_emoji_id=ADMIN_PRICE_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Сервера",
            callback_data="admin_servers",
            style="primary",
            icon_custom_emoji_id=ADMIN_SERVERS_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Выдать подписку",
            callback_data="admin_give_subscription",
            style="success",
            icon_custom_emoji_id=GIVE_SUBSCRIPTION_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Забрать подписку",
            callback_data="admin_take_subscription",
            style="danger",
            icon_custom_emoji_id=TAKE_SUBSCRIPTION_EMOJI_ID
        )
    )
    return builder.as_markup()

def get_give_subscription_plan_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Solo",
            callback_data="admin_give_plan_solo",
            style="primary",
            icon_custom_emoji_id=SOLO_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Premium",
            callback_data="admin_give_plan_premium",
            style="primary",
            icon_custom_emoji_id=PREMIUM_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Family",
            callback_data="admin_give_plan_family",
            style="primary",
            icon_custom_emoji_id=FAMILY_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data="admin_panel"
        )
    )
    return builder.as_markup()

def get_admin_back_keyboard(callback_data: str = "admin_panel"):
    builder = InlineKeyboardBuilder()
    builder.button(text="« Назад", callback_data=callback_data, style="default")
    return builder.as_markup()

def get_cancel_keyboard(back_callback: str = "admin_panel"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Отмена",
        callback_data=back_callback,
        style="danger",
        icon_custom_emoji_id=CANCEL_EMOJI_ID
    )
    return builder.as_markup()

def get_confirm_keyboard(confirm_callback: str, cancel_callback: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data=confirm_callback,
            style="success",
            icon_custom_emoji_id=CHECK_EMOJI_NEW_ID
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data=cancel_callback,
            style="danger",
            icon_custom_emoji_id=ADMIN_CROSS_EMOJI_ID
        )
    )
    return builder.as_markup()

def get_servers_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Количество серверов",
            callback_data="admin_servers_count",
            style="primary",
            icon_custom_emoji_id=SERVERS_COUNT_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Удалить сервер",
            callback_data="admin_server_remove",
            style="danger",
            icon_custom_emoji_id=ADMIN_CROSS_EMOJI_ID
        ),
        InlineKeyboardButton(
            text="Добавить сервер",
            callback_data="admin_server_add",
            style="success",
            icon_custom_emoji_id=PLUS_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Очистить все серверы",
            callback_data="admin_server_clear",
            style="danger",
            icon_custom_emoji_id=SERVERS_CLEAR_EMOJI_ID
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin_panel", style="default")
    )
    return builder.as_markup()

def get_broadcast_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Своя рассылка",
            callback_data="broadcast_custom",
            style="success"
        ),
        InlineKeyboardButton(
            text="Готовая рассылка",
            callback_data="broadcast_ready",
            style="primary"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin_panel", style="default")
    )
    return builder.as_markup()