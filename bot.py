import logging
import os
import json
import uuid
import time
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# ============================================================
# 1. НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# 2. КОНФИГУРАЦИЯ БОТА
# ============================================================
TOKEN = "8578762350:AAFrd1SgZzm7IvELjcwrj6anShyzHeZlCws"
ADMIN_IDS = [8400055743, 8297446667]  # владельцы
BANNER_URL = "https://i.ibb.co/7dTv2VP4/IMG-1367.jpg"
SUPPORT_URL = "https://forms.gle/4kN2r57SJiPrxBjf9"
GUIDE_URL = "https://telegra.ph/Podrobnyj-gajd-po-ispolzovaniyu-GiftElfRobot-04-25"
BOT_USERNAME = "GiftElfiliRobot"
REFERRAL_PERCENT = 20

# Файлы для хранения данных
ADMINS_FILE = "admins.json"
LOGS_FILE = "bot_logs.json"

# ============================================================
# 3. ПРЕМИУМ-ЭМОДЗИ
# ============================================================
EMOJI_TAGS = {
    "rocket": '<tg-emoji emoji-id="5195033767969839232">🚀</tg-emoji>',
    "shield": '<tg-emoji emoji-id="5197288647275071607">🛡</tg-emoji>',
    "pin": '<tg-emoji emoji-id="5258461531464539536">📌</tg-emoji>',
    "pen": '<tg-emoji emoji-id="5197269100878907942">✍️</tg-emoji>',
    "money": '<tg-emoji emoji-id="5287231198098117669">💰</tg-emoji>',
    "money2": '<tg-emoji emoji-id="5278467510604160626">💰</tg-emoji>',
    "check": '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji>',
    "receipt": '<tg-emoji emoji-id="5444856076954520455">🧾</tg-emoji>',
    "briefcase": '<tg-emoji emoji-id="5893255507380014983">💼</tg-emoji>',
    "heart": '<tg-emoji emoji-id="5265074015868822600">❤️</tg-emoji>',
    "card": '<tg-emoji emoji-id="5445353829304387411">💳</tg-emoji>',
    "star": '<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji>',
    "coin": '<tg-emoji emoji-id="5377620962390857342">🪙</tg-emoji>',
    "coin2": '<tg-emoji emoji-id="5264713049637409446">🪙</tg-emoji>',
    "chart": '<tg-emoji emoji-id="5190806721286657692">📊</tg-emoji>',
    "globe": '<tg-emoji emoji-id="5447410659077661506">🌐</tg-emoji>',
    "users": '<tg-emoji emoji-id="5958460691550572213">👥</tg-emoji>',
    "wallet": '<tg-emoji emoji-id="5445353829304387411">💳</tg-emoji>',
    "link": '<tg-emoji emoji-id="5206607081334906820">🔗</tg-emoji>',
    "phone": '<tg-emoji emoji-id="5444856076954520455">📞</tg-emoji>'
}
SYMBOLS = {k: v.split('>')[1].split('<')[0] for k, v in EMOJI_TAGS.items()}

# ============================================================
# 4. ЛОКАЛИЗАЦИЯ (без f-строк)
# ============================================================
LANGUAGES = {
    "ru": {
        "name": "Русский",
        "welcome": (
            "{rocket} <b>Добро пожаловать в ELF OTC – надёжный P2P-гарант</b>\n\n"
            "<b>Покупайте и продавайте всё, что угодно – безопасно!</b>\n"
            "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
            "• Удобное управление кошельками\n"
            "• Реферальная система\n\n"
            "<b>Как пользоваться?</b>\n"
            "Ознакомьтесь с инструкцией —\n"
            "<a href='{guide_url}'>Подробный гайд по использованию</a>\n\n"
            "Выберите нужный раздел ниже:"
        ),
        "main_menu": "Главное меню",
        "wallet_menu": (
            "{wallet} <b>Ваш текущий кошелек:</b>\n"
            "Выбрана оплата в <b>{method}</b>\n\n"
            "Вы можете изменить способ оплаты ниже:"
        ),
        "wallet_ton_add": "{pen} <b>Добавление TON-кошелька</b>\n\nПожалуйста, введите ваш TON адрес",
        "wallet_sbp_add": (
            "{pen} <b>Добавление СБП</b>\n\n"
            "Пожалуйста, введите номер телефона в формате:\n<code>+7(ХХХ)ХХХ-ХХ-ХХ</code>"
        ),
        "wallet_sbp_bank": "{pen} Пожалуйста, уточните, какой у вас банк!",
        "wallet_card_add": (
            "{pen} <b>Добавление банковской карты</b>\n\n"
            "Пожалуйста, введите номер банковской карты в формате:\n<code>XXXX XXXX XXXX XXXX</code>"
        ),
        "wallet_card_bank": "{pen} Пожалуйста, уточните, какой у вас банк!",
        "wallet_stars_updated": "{check} <b>Настройки обновлены:</b>\nвалюта сделок — STARS",
        "wallet_ton_success": "{check} TON-кошелек успешно добавлен!",
        "wallet_sbp_success": "{check} Кошелек успешно добавлен/изменен!",
        "wallet_card_success": "{check} Кошелек успешно добавлен/изменен!",
        "create_deal_title": "{money} <b>Создание сделки</b>\n\nВведите сумму STARS в формате:\n<code>2000</code>",
        "create_deal_desc": "{pen} <b>Укажите, что вы предлагаете в этой сделке:</b>\n\n<i>Пример: 10 Кепок и Пене...</i>",
        "create_deal_success": (
            "{check} <b>Сделка успешно создана!</b>\n\n"
            "Сумма: <b>{amount} STARS</b>\n\n"
            "<b>Описание:</b>\n{description}\n\n"
            "Ссылка для покупателя:\n<code>{link}</code>\n\n"
            "<i>dev: @seinarukiro</i>\n<i>t.me/otcgifttg</i>"
        ),
        "deal_info": (
            "{money} <b>Информация о сделке</b>\n\n"
            "Сумма: <b>{amount} STARS</b>\n"
            "Описание: {description}\n\n"
            "Для подтверждения сделки нажмите кнопку ниже."
        ),
        "deal_confirmed": "✅ Сделка подтверждена и завершена!",
        "deal_canceled": "❌ Сделка отменена.",
        "deal_not_found": "❌ Сделка не найдена или уже неактивна.",
        "ref_title": (
            "{link_emoji} <b>Ваша реферальная ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "Количество рефералов: {refs}\n"
            "Заработано с рефералов: {earned} RUB\n"
            "Вы получаете {percent}% от комиссии бота с рефералов."
        ),
        "lang_title": "{globe} <b>Choose your language:</b>\n\nВыберите язык:",
        "lang_changed": "🌐 Язык изменён на {lang}",
        "support_title": "{phone} <b>Техническая поддержка</b>\n\nДля связи с нами заполните форму:\n<a href='{support_url}'>Нажмите здесь</a>",
        "back_to_menu": "↩️ Вернуться в меню",
        "btn_wallet": "{wallet_symbol} Добавить/изменить кошелёк",
        "btn_create_deal": "{money_symbol} Создать сделку",
        "btn_ref": "{link_symbol} Реферальная ссылка",
        "btn_lang": "{globe_symbol} Сменить язык",
        "btn_support": "{phone_symbol} Поддержка",
        "btn_ton": "➕ Добавить TON-кошелек",
        "btn_sbp": "➕ Добавить СБП",
        "btn_card_rf": "➕ Добавить банковскую карту (РФ)",
        "btn_card_ua": "➕ Добавить банковскую карту (UA)",
        "btn_stars": "⭐ Оплата в STARS",
        "btn_confirm": "✅ Подтвердить сделку",
        "btn_cancel": "❌ Отменить",
        "btn_cancel_deal": "❌ Отменить сделку",
        "btn_back": "↩️ Вернуться в меню",
        "admin_panel": (
            "{star} <b>Админ-панель</b>\n\n"
            "/wrfas – список команд\n"
            "/buyslnft <ID> – завершить сделку\n"
            "/vidach <user_id> <сумма> – пополнить баланс\n"
            "/sdelkibo <user_id> – накрутить сделки"
        ),
        "help_text": "{pin} <b>Доступные команды:</b>\n/start – главное меню\n/help – эта справка",
        "invalid_amount": "⚠️ Пожалуйста, введите корректное положительное число.",
        "invalid_description": "⚠️ Описание не может быть пустым. Попробуйте ещё раз.",
        "invalid_ton": "⚠️ Похоже, адрес слишком короткий. Попробуйте ещё раз.",
        "invalid_phone": "⚠️ Неверный формат. Попробуйте ещё раз.",
        "invalid_card": "⚠️ Неверный формат карты. Должно быть 16 цифр.",
        "invalid_bank": "⚠️ Введите название банка.",
        "deal_canceled_by_user": "❌ Создание сделки отменено.",
        "something_wrong": "❌ Что-то пошло не так. Начните заново через /start",
    },
    "en": {
        "name": "English",
        "welcome": (
            "{rocket} <b>Welcome to ELF OTC – trusted P2P escrow</b>\n\n"
            "<b>Buy and sell anything – safely!</b>\n"
            "From Telegram gifts and NFT to tokens and fiat – deals are easy and risk-free.\n\n"
            "• Convenient wallet management\n"
            "• Referral system\n\n"
            "<b>How to use?</b>\n"
            "Check out the guide —\n"
            "<a href='{guide_url}'>Detailed guide</a>\n\n"
            "Select a section below:"
        ),
        "main_menu": "Main menu",
        "wallet_menu": (
            "{wallet} <b>Your current wallet:</b>\n"
            "Selected payment method: <b>{method}</b>\n\n"
            "You can change payment method below:"
        ),
        "wallet_ton_add": "{pen} <b>Adding TON wallet</b>\n\nPlease enter your TON address",
        "wallet_sbp_add": (
            "{pen} <b>Adding SBP</b>\n\n"
            "Please enter your phone number in format:\n<code>+7(XXX)XXX-XX-XX</code>"
        ),
        "wallet_sbp_bank": "{pen} Please specify your bank!",
        "wallet_card_add": (
            "{pen} <b>Adding bank card</b>\n\n"
            "Please enter your card number in format:\n<code>XXXX XXXX XXXX XXXX</code>"
        ),
        "wallet_card_bank": "{pen} Please specify your bank!",
        "wallet_stars_updated": "{check} <b>Settings updated:</b>\ncurrency for deals — STARS",
        "wallet_ton_success": "{check} TON wallet successfully added!",
        "wallet_sbp_success": "{check} Wallet successfully added/changed!",
        "wallet_card_success": "{check} Wallet successfully added/changed!",
        "create_deal_title": "{money} <b>Create deal</b>\n\nEnter amount in STARS:\n<code>2000</code>",
        "create_deal_desc": "{pen} <b>What are you offering in this deal?</b>\n\n<i>Example: 10 Caps and Pen...</i>",
        "create_deal_success": (
            "{check} <b>Deal successfully created!</b>\n\n"
            "Amount: <b>{amount} STARS</b>\n\n"
            "<b>Description:</b>\n{description}\n\n"
            "Link for buyer:\n<code>{link}</code>\n\n"
            "<i>dev: @seinarukiro</i>\n<i>t.me/otcgifttg</i>"
        ),
        "deal_info": (
            "{money} <b>Deal info</b>\n\n"
            "Amount: <b>{amount} STARS</b>\n"
            "Description: {description}\n\n"
            "Press button below to confirm the deal."
        ),
        "deal_confirmed": "✅ Deal confirmed and completed!",
        "deal_canceled": "❌ Deal canceled.",
        "deal_not_found": "❌ Deal not found or already inactive.",
        "ref_title": (
            "{link_emoji} <b>Your referral link:</b>\n"
            "<code>{link}</code>\n\n"
            "Referrals: {refs}\n"
            "Earned from referrals: {earned} RUB\n"
            "You get {percent}% of bot's commission from referrals."
        ),
        "lang_title": "{globe} <b>Choose your language:</b>\n\nВыберите язык:",
        "lang_changed": "🌐 Language changed to {lang}",
        "support_title": "{phone} <b>Support</b>\n\nTo contact us, fill out the form:\n<a href='{support_url}'>Click here</a>",
        "back_to_menu": "↩️ Back to menu",
        "btn_wallet": "{wallet_symbol} Add/change wallet",
        "btn_create_deal": "{money_symbol} Create deal",
        "btn_ref": "{link_symbol} Referral link",
        "btn_lang": "{globe_symbol} Change language",
        "btn_support": "{phone_symbol} Support",
        "btn_ton": "➕ Add TON wallet",
        "btn_sbp": "➕ Add SBP",
        "btn_card_rf": "➕ Add bank card (RU)",
        "btn_card_ua": "➕ Add bank card (UA)",
        "btn_stars": "⭐ Pay in STARS",
        "btn_confirm": "✅ Confirm deal",
        "btn_cancel": "❌ Cancel",
        "btn_cancel_deal": "❌ Cancel deal",
        "btn_back": "↩️ Back to menu",
        "admin_panel": (
            "{star} <b>Admin panel</b>\n\n"
            "/wrfas – list of commands\n"
            "/buyslnft <ID> – complete deal\n"
            "/vidach <user_id> <amount> – add balance\n"
            "/sdelkibo <user_id> – fake deals"
        ),
        "help_text": "{pin} <b>Available commands:</b>\n/start – main menu\n/help – this help",
        "invalid_amount": "⚠️ Please enter a valid positive number.",
        "invalid_description": "⚠️ Description cannot be empty. Try again.",
        "invalid_ton": "⚠️ Address seems too short. Try again.",
        "invalid_phone": "⚠️ Invalid format. Try again.",
        "invalid_card": "⚠️ Invalid card format. Must be 16 digits.",
        "invalid_bank": "⚠️ Please enter your bank name.",
        "deal_canceled_by_user": "❌ Deal creation canceled.",
        "something_wrong": "❌ Something went wrong. Start over with /start",
    }
}

# ============================================================
# 5. СОСТОЯНИЯ ДЛЯ ДИАЛОГОВ
# ============================================================
AMOUNT, DESCRIPTION = range(2)
(
    WALLET_MAIN,
    WALLET_TON_INPUT,
    WALLET_SBP_PHONE,
    WALLET_SBP_BANK,
    WALLET_CARD_RF_INPUT,
    WALLET_CARD_RF_BANK,
    WALLET_CARD_UA_INPUT,
    WALLET_CARD_UA_BANK,
    ADMIN_ADD_USER,
    ADMIN_ADD_TIME,
) = range(2, 12)

# ============================================================
# 6. ХРАНИЛИЩА
# ============================================================
balances = {}
deals = {}
user_deals = {}
deal_counter = 0
temp_deal_data = {}
wallets = {}
user_lang = {}
referrals = {}
referral_earnings = {}

# Админ-данные: {user_id: {'expires': timestamp or None, 'added_by': user_id, 'added_at': timestamp}}
admin_data = {}
admin_logs = []  # список логов (каждый лог - dict)

def load_data():
    global admin_data, admin_logs
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r') as f:
                admin_data = json.load(f)
        except:
            admin_data = {}
    else:
        admin_data = {}
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r') as f:
                admin_logs = json.load(f)
        except:
            admin_logs = []
    else:
        admin_logs = []

def save_admins():
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admin_data, f)

def save_logs():
    # Оставляем только последние 1000 записей
    if len(admin_logs) > 1000:
        admin_logs = admin_logs[-1000:]
    with open(LOGS_FILE, 'w') as f:
        json.dump(admin_logs, f)

def log_action(user_id, username, action, details=""):
    """Запись действия в логи"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "username": username,
        "action": action,
        "details": details
    }
    admin_logs.append(entry)
    save_logs()

def get_user_identifier(update: Update) -> tuple:
    """Возвращает (user_id, username) с blur для username"""
    user = update.effective_user
    uid = user.id
    uname = user.username if user.username else "no_username"
    # blur: показываем только первую и последнюю букву
    if len(uname) > 3:
        uname_blur = uname[0] + "..." + uname[-1]
    else:
        uname_blur = uname
    return uid, uname_blur

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом (владельцем или добавленным)"""
    if user_id in ADMIN_IDS:
        return True
    # Проверяем временных админов
    if user_id in admin_data:
        expires = admin_data[user_id].get('expires')
        if expires is None:
            return True  # бессрочный
        if expires > time.time():
            return True
        else:
            # Удаляем истекшего админа
            del admin_data[user_id]
            save_admins()
    return False

def is_owner(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ============================================================
# 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, 'ru')

def get_text(key: str, user_id: int, **kwargs) -> str:
    lang = get_lang(user_id)
    template = LANGUAGES.get(lang, LANGUAGES['ru']).get(key, key)
    format_dict = {
        'rocket': EMOJI_TAGS['rocket'],
        'shield': EMOJI_TAGS['shield'],
        'pin': EMOJI_TAGS['pin'],
        'pen': EMOJI_TAGS['pen'],
        'money': EMOJI_TAGS['money'],
        'money2': EMOJI_TAGS['money2'],
        'check': EMOJI_TAGS['check'],
        'receipt': EMOJI_TAGS['receipt'],
        'briefcase': EMOJI_TAGS['briefcase'],
        'heart': EMOJI_TAGS['heart'],
        'card': EMOJI_TAGS['card'],
        'star': EMOJI_TAGS['star'],
        'coin': EMOJI_TAGS['coin'],
        'coin2': EMOJI_TAGS['coin2'],
        'chart': EMOJI_TAGS['chart'],
        'globe': EMOJI_TAGS['globe'],
        'users': EMOJI_TAGS['users'],
        'wallet': EMOJI_TAGS['wallet'],
        'link_emoji': EMOJI_TAGS['link'],
        'phone': EMOJI_TAGS['phone'],
        'guide_url': GUIDE_URL,
        'support_url': SUPPORT_URL,
        'wallet_symbol': SYMBOLS['wallet'],
        'money_symbol': SYMBOLS['money'],
        'link_symbol': SYMBOLS['link'],
        'globe_symbol': SYMBOLS['globe'],
        'phone_symbol': SYMBOLS['phone'],
        'star_symbol': SYMBOLS['star'],
    }
    format_dict.update(kwargs)
    try:
        return template.format(**format_dict)
    except KeyError as e:
        logger.error(f"Missing key in translation: {e}")
        return template

def get_wallet(user_id: int) -> dict:
    if user_id not in wallets:
        wallets[user_id] = {
            "ton": None,
            "sbp": None,
            "card_rf": None,
            "card_ua": None,
            "payment_method": "stars"
        }
    return wallets[user_id]

def generate_ref_code() -> str:
    return uuid.uuid4().hex[:12]

def create_deal(creator_id: int, amount: float, description: str) -> dict:
    global deal_counter
    deal_counter += 1
    deal_id = deal_counter
    deal_code = f"deal_{uuid.uuid4().hex[:8]}"
    deal = {
        "id": deal_id,
        "creator": creator_id,
        "amount": amount,
        "description": description,
        "status": "active",
        "code": deal_code,
        "buyer_link": f"https://t.me/{BOT_USERNAME}?start={deal_code}"
    }
    deals[deal_id] = deal
    user_deals.setdefault(creator_id, []).append(deal_id)
    log_action(creator_id, f"user_{creator_id}", "create_deal", f"Создана сделка #{deal_id} на {amount} STARS")
    return deal

def get_deal_by_code(code: str):
    for deal in deals.values():
        if deal.get("code") == code:
            return deal
    return None

# ============================================================
# 8. ГЛАВНОЕ МЕНЮ (БЕЗ КНОПКИ АДМИНА)
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    log_action(user_id, username, "start", "Запуск бота")
    if context.args:
        code = context.args[0]
        if code.startswith("deal_"):
            deal = get_deal_by_code(code)
            if deal and deal["status"] == "active":
                await show_deal_to_buyer(update, context, deal)
                return
            else:
                await update.message.reply_text(get_text("deal_not_found", user_id))
                return
        elif code.startswith("ref_"):
            referrer_id = int(code.split("_")[1])
            if referrer_id != user_id:
                if user_id not in referrals.get(referrer_id, []):
                    referrals.setdefault(referrer_id, []).append(user_id)
                    referral_earnings[referrer_id] = referral_earnings.get(referrer_id, 0) + 0.5
                    log_action(user_id, username, "referral", f"Зарегистрирован по реферальной ссылке от {referrer_id}")
                await update.message.reply_text("✅ Вы успешно зарегистрированы по реферальной ссылке!")
            else:
                await update.message.reply_text("ℹ️ Вы не можете пригласить самого себя.")
            await show_main_menu(update, context)
            return

    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    caption = get_text("welcome", user_id)
    keyboard = [
        [InlineKeyboardButton(get_text("btn_wallet", user_id), callback_data='wallet')],
        [InlineKeyboardButton(get_text("btn_create_deal", user_id), callback_data='create_deal')],
        [InlineKeyboardButton(get_text("btn_ref", user_id), callback_data='ref')],
        [InlineKeyboardButton(get_text("btn_lang", user_id), callback_data='lang')],
        [InlineKeyboardButton(get_text("btn_support", user_id), callback_data='support')],
    ]
    # Кнопка админа УДАЛЕНА
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=BANNER_URL,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=BANNER_URL,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def show_deal_to_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE, deal: dict):
    user_id = update.effective_user.id
    text = get_text("deal_info", user_id, amount=deal['amount'], description=deal['description'])
    keyboard = [
        [InlineKeyboardButton(get_text("btn_confirm", user_id), callback_data=f"confirm_deal_{deal['id']}")],
        [InlineKeyboardButton(get_text("btn_cancel", user_id), callback_data=f"cancel_deal_{deal['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

# ============================================================
# 9. ДИАЛОГ СОЗДАНИЯ СДЕЛКИ
# ============================================================
async def create_deal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("create_deal_title", user_id),
        parse_mode='HTML'
    )
    log_action(user_id, username, "create_deal_start", "Начало создания сделки")
    return AMOUNT

async def create_deal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(get_text("invalid_amount", user_id))
        return AMOUNT

    temp_deal_data[user_id] = {"amount": amount}
    await update.message.reply_text(get_text("create_deal_desc", user_id), parse_mode='HTML')
    log_action(user_id, username, "create_deal_amount", f"Введена сумма {amount}")
    return DESCRIPTION

async def create_deal_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    description = update.message.text.strip()
    if not description:
        await update.message.reply_text(get_text("invalid_description", user_id))
        return DESCRIPTION

    data = temp_deal_data.get(user_id)
    if not data:
        await update.message.reply_text(get_text("something_wrong", user_id))
        return ConversationHandler.END

    amount = data["amount"]
    deal = create_deal(user_id, amount, description)

    text = get_text("create_deal_success", user_id,
                    amount=int(amount),
                    description=description,
                    link=deal['buyer_link'])
    keyboard = [
        [InlineKeyboardButton(get_text("btn_cancel_deal", user_id), callback_data=f"cancel_deal_{deal['id']}")],
        [InlineKeyboardButton(get_text("btn_back", user_id), callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

    log_action(user_id, username, "create_deal_finish", f"Создана сделка #{deal['id']}: {description}")
    if user_id in temp_deal_data:
        del temp_deal_data[user_id]

    return ConversationHandler.END

async def cancel_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"
    if user_id in temp_deal_data:
        del temp_deal_data[user_id]
    await update.message.reply_text(get_text("deal_canceled_by_user", user_id))
    log_action(user_id, username, "cancel_dialog", "Отмена создания сделки")
    await show_main_menu(update, context)
    return ConversationHandler.END

# ============================================================
# 10. ДИАЛОГ УПРАВЛЕНИЯ КОШЕЛЬКАМИ (без изменений)
# ============================================================
# ... (весь код кошелька остаётся без изменений, он слишком длинный, но мы его сохраняем)
# Для краткости я пропущу его в этом ответе, но в финальном файле он будет.

# ============================================================
# 11. АДМИН-КОМАНДЫ (НОВЫЕ)
# ============================================================
async def wrfas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список админ-команд (доступно админам и владельцам)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    text = (
        f"{EMOJI_TAGS['star']} <b>Доступные админ-команды:</b>\n\n"
        f"🔹 <code>/wrfas</code> – показать этот список\n"
        f"🔹 <code>/buyslnft &lt;ID_сделки&gt;</code> – завершить сделку (начислить продавцу)\n"
        f"🔹 <code>/vidach &lt;user_id&gt; &lt;сумма&gt;</code> – пополнить баланс пользователя\n"
        f"🔹 <code>/sdelkibo &lt;user_id&gt;</code> – создать фиктивные сделки для теста\n"
        f"🔹 <code>/setadminis</code> – управление админами (только для владельцев)"
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def setadminis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление админами (только для владельцев)"""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Эта команда доступна только владельцам бота.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📋 <b>Использование:</b>\n"
            "<code>/setadminis add &lt;user_id&gt; [время]</code> – добавить админа (время: 1d, 2h, 30m, 1w, 1M)\n"
            "<code>/setadminis remove &lt;user_id&gt;</code> – удалить админа\n"
            "<code>/setadminis list</code> – список админов\n"
            "<code>/setadminis logs [кол-во]</code> – показать логи (по умолчанию 10)\n"
            "<code>/setadminis export</code> – экспортировать логи в файл",
            parse_mode='HTML'
        )
        return

    subcommand = args[0].lower()

    if subcommand == "add":
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите ID пользователя: /setadminis add <user_id> [время]")
            return
        try:
            target_id = int(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ ID должен быть числом.")
            return

        expires = None
        if len(args) >= 3:
            time_str = args[2]
            # Парсим время: 1d, 2h, 30m, 1w, 1M
            unit = time_str[-1]
            try:
                value = int(time_str[:-1])
            except:
                await update.message.reply_text("⚠️ Неверный формат времени. Используйте: 1d, 2h, 30m, 1w, 1M")
                return
            if unit == 'd':
                expires = time.time() + value * 86400
            elif unit == 'h':
                expires = time.time() + value * 3600
            elif unit == 'm':
                expires = time.time() + value * 60
            elif unit == 'w':
                expires = time.time() + value * 604800
            elif unit == 'M':
                expires = time.time() + value * 2592000  # ~30 дней
            else:
                await update.message.reply_text("⚠️ Неизвестная единица времени. Используйте: d, h, m, w, M")
                return

        admin_data[target_id] = {
            "expires": expires,
            "added_by": user_id,
            "added_at": time.time()
        }
        save_admins()
        log_action(user_id, update.effective_user.username or "no_username", "setadminis_add", f"Добавлен админ {target_id}" + (f" на {time_str}" if expires else " бессрочно"))
        await update.message.reply_text(f"✅ Пользователь {target_id} добавлен в админы." + (f" до {datetime.fromtimestamp(expires).strftime('%Y-%m-%d %H:%M')}" if expires else " бессрочно."))

    elif subcommand == "remove":
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите ID пользователя: /setadminis remove <user_id>")
            return
        try:
            target_id = int(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ ID должен быть числом.")
            return
        if target_id in admin_data:
            del admin_data[target_id]
            save_admins()
            log_action(user_id, update.effective_user.username or "no_username", "setadminis_remove", f"Удалён админ {target_id}")
            await update.message.reply_text(f"✅ Пользователь {target_id} удалён из админов.")
        else:
            await update.message.reply_text(f"❌ Пользователь {target_id} не является админом.")

    elif subcommand == "list":
        if not admin_data:
            await update.message.reply_text("📋 Список админов пуст.")
            return
        text = "📋 <b>Список админов:</b>\n\n"
        for uid, data in admin_data.items():
            expires = data.get('expires')
            if expires:
                time_left = expires - time.time()
                if time_left > 0:
                    days = int(time_left // 86400)
                    hours = int((time_left % 86400) // 3600)
                    minutes = int((time_left % 3600) // 60)
                    time_str = f"{days}д {hours}ч {minutes}м"
                else:
                    time_str = "⚠️ Истекло (будет удалён при следующей проверке)"
            else:
                time_str = "♾️ Бессрочно"
            added_by = data.get('added_by', 'неизвестно')
            text += f"🔹 <code>{uid}</code> – {time_str} (добавил: {added_by})\n"
        await update.message.reply_text(text, parse_mode='HTML')

    elif subcommand == "logs":
        count = 10
        if len(args) > 1:
            try:
                count = int(args[1])
            except:
                count = 10
        if not admin_logs:
            await update.message.reply_text("📋 Логов пока нет.")
            return
        # Берём последние count записей
        logs = admin_logs[-count:]
        text = "📋 <b>Последние логи:</b>\n\n"
        for entry in reversed(logs):
            ts = entry.get('timestamp', '')
            uid = entry.get('user_id', '')
            uname = entry.get('username', '')
            action = entry.get('action', '')
            details = entry.get('details', '')
            text += f"<code>{ts}</code> | {uid} (@{uname}) | {action} | {details}\n"
            if len(text) > 4000:
                text += "... (обрезано)"
                break
        await update.message.reply_text(text, parse_mode='HTML')

    elif subcommand == "export":
        if not admin_logs:
            await update.message.reply_text("📋 Логов нет для экспорта.")
            return
        # Создаём файл с логами
        filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(admin_logs, f, indent=2)
        await update.message.reply_document(document=open(filename, 'rb'), filename=filename)
        os.remove(filename)

    else:
        await update.message.reply_text("❌ Неизвестная подкоманда. Используйте add, remove, list, logs, export.")

# ============================================================
# 12. ОСТАЛЬНЫЕ АДМИН-КОМАНДЫ (buyslnft, vidach, sdelkibo) - без изменений
# ============================================================
# ... они уже есть в коде, оставляем как есть.

# ============================================================
# 13. ЗАПУСК
# ============================================================
def main():
    load_data()
    application = Application.builder().token(TOKEN).build()

    # ... (регистрация хендлеров, ConversationHandler)
    # Полный код регистрации будет в финальном файле.

    port = int(os.environ.get("PORT", 10000))
    external_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if external_url:
        webhook_url = f"https://{external_url}/webhook"
        logger.info(f"Запуск с вебхуком: {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=webhook_url
        )
    else:
        logger.info("Запуск в режиме polling (локально)")
        application.run_polling()

if __name__ == '__main__':
    main()
