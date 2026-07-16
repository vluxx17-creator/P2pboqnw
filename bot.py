import logging
import os
import uuid
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
ADMIN_IDS = [8400055743, 8297446667]
BANNER_URL = "https://i.ibb.co/7dTv2VP4/IMG-1367.jpg"
SUPPORT_URL = "https://forms.gle/4kN2r57SJiPrxBjf9"
GUIDE_URL = "https://telegra.ph/Podrobnyj-gajd-po-ispolzovaniyu-GiftElfRobot-04-25"
BOT_USERNAME = "GiftElfiliRobot"
REFERRAL_PERCENT = 20  # 20% от комиссии

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
# 4. ЛОКАЛИЗАЦИЯ (БЕЗ f-СТРОК)
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
        "btn_admin": "{star_symbol} Админ-панель",
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
        "btn_admin": "{star_symbol} Admin panel",
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
) = range(2, 10)

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

def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, 'ru')

def get_text(key: str, user_id: int, **kwargs) -> str:
    lang = get_lang(user_id)
    template = LANGUAGES.get(lang, LANGUAGES['ru']).get(key, key)
    # Подставляем эмодзи и другие переменные
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

# ============================================================
# 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_balance(user_id: int) -> float:
    return balances.get(user_id, 0.0)

def add_balance(user_id: int, amount: float) -> None:
    balances[user_id] = get_balance(user_id) + amount

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
    return deal

def get_deal_by_code(code: str):
    for deal in deals.values():
        if deal.get("code") == code:
            return deal
    return None

# ============================================================
# 8. ГЛАВНОЕ МЕНЮ
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(get_text("btn_admin", user_id), callback_data='admin_panel')])
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
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("create_deal_title", user_id),
        parse_mode='HTML'
    )
    return AMOUNT

async def create_deal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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
    return DESCRIPTION

async def create_deal_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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

    if user_id in temp_deal_data:
        del temp_deal_data[user_id]

    return ConversationHandler.END

async def cancel_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in temp_deal_data:
        del temp_deal_data[user_id]
    await update.message.reply_text(get_text("deal_canceled_by_user", user_id))
    await show_main_menu(update, context)
    return ConversationHandler.END

# ============================================================
# 10. ДИАЛОГ УПРАВЛЕНИЯ КОШЕЛЬКАМИ
# ============================================================
async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)

    method_names = {
        "stars": "STARS",
        "ton": "TON",
        "sbp": "СБП",
        "card_rf": "Card (RF)",
        "card_ua": "Card (UA)"
    }
    current = method_names.get(wallet["payment_method"], "STARS")
    text = get_text("wallet_menu", user_id, method=current)

    keyboard = [
        [InlineKeyboardButton(get_text("btn_ton", user_id), callback_data="wallet_ton")],
        [InlineKeyboardButton(get_text("btn_sbp", user_id), callback_data="wallet_sbp")],
        [InlineKeyboardButton(get_text("btn_card_rf", user_id), callback_data="wallet_card_rf")],
        [InlineKeyboardButton(get_text("btn_card_ua", user_id), callback_data="wallet_card_ua")],
        [InlineKeyboardButton(get_text("btn_stars", user_id), callback_data="wallet_stars")],
        [InlineKeyboardButton(get_text("btn_back", user_id), callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return WALLET_MAIN

async def wallet_ton_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("wallet_ton_add", user_id),
        parse_mode='HTML'
    )
    return WALLET_TON_INPUT

async def wallet_ton_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ton_address = update.message.text.strip()
    if len(ton_address) < 10:
        await update.message.reply_text(get_text("invalid_ton", user_id))
        return WALLET_TON_INPUT

    wallet = get_wallet(user_id)
    wallet["ton"] = ton_address
    wallet["payment_method"] = "ton"

    await update.message.reply_text(
        f"{get_text('wallet_ton_success', user_id)}\n\n<b>Address:</b>\n<code>{ton_address}</code>",
        parse_mode='HTML'
    )
    return await wallet_menu(update, context)

async def wallet_sbp_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("wallet_sbp_add", user_id),
        parse_mode='HTML'
    )
    return WALLET_SBP_PHONE

async def wallet_sbp_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    if not phone.startswith('+') or len(phone) < 10:
        await update.message.reply_text(get_text("invalid_phone", user_id))
        return WALLET_SBP_PHONE

    context.user_data['sbp_phone'] = phone
    await update.message.reply_text(get_text("wallet_sbp_bank", user_id), parse_mode='HTML')
    return WALLET_SBP_BANK

async def wallet_sbp_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bank = update.message.text.strip()
    if not bank:
        await update.message.reply_text(get_text("invalid_bank", user_id))
        return WALLET_SBP_BANK

    wallet = get_wallet(user_id)
    wallet["sbp"] = {"phone": context.user_data.get('sbp_phone'), "bank": bank}
    wallet["payment_method"] = "sbp"

    await update.message.reply_text(
        f"{get_text('wallet_sbp_success', user_id)}\n\n<b>SBP:</b>\nPhone: {context.user_data['sbp_phone']}\nBank: {bank}",
        parse_mode='HTML'
    )
    if 'sbp_phone' in context.user_data:
        del context.user_data['sbp_phone']
    return await wallet_menu(update, context)

async def wallet_card_rf_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("wallet_card_add", user_id),
        parse_mode='HTML'
    )
    return WALLET_CARD_RF_INPUT

async def wallet_card_rf_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = update.message.text.strip().replace(' ', '')
    if len(card) != 16 or not card.isdigit():
        await update.message.reply_text(get_text("invalid_card", user_id))
        return WALLET_CARD_RF_INPUT

    context.user_data['card_rf'] = card
    await update.message.reply_text(get_text("wallet_card_bank", user_id), parse_mode='HTML')
    return WALLET_CARD_RF_BANK

async def wallet_card_rf_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bank = update.message.text.strip()
    if not bank:
        await update.message.reply_text(get_text("invalid_bank", user_id))
        return WALLET_CARD_RF_BANK

    wallet = get_wallet(user_id)
    wallet["card_rf"] = {"card": context.user_data['card_rf'], "bank": bank}
    wallet["payment_method"] = "card_rf"

    await update.message.reply_text(
        f"{get_text('wallet_card_success', user_id)}\n\n<b>Card (RF):</b>\nNumber: {context.user_data['card_rf']}\nBank: {bank}",
        parse_mode='HTML'
    )
    if 'card_rf' in context.user_data:
        del context.user_data['card_rf']
    return await wallet_menu(update, context)

async def wallet_card_ua_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("wallet_card_add", user_id),
        parse_mode='HTML'
    )
    return WALLET_CARD_UA_INPUT

async def wallet_card_ua_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    card = update.message.text.strip().replace(' ', '')
    if len(card) != 16 or not card.isdigit():
        await update.message.reply_text(get_text("invalid_card", user_id))
        return WALLET_CARD_UA_INPUT

    context.user_data['card_ua'] = card
    await update.message.reply_text(get_text("wallet_card_bank", user_id), parse_mode='HTML')
    return WALLET_CARD_UA_BANK

async def wallet_card_ua_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bank = update.message.text.strip()
    if not bank:
        await update.message.reply_text(get_text("invalid_bank", user_id))
        return WALLET_CARD_UA_BANK

    wallet = get_wallet(user_id)
    wallet["card_ua"] = {"card": context.user_data['card_ua'], "bank": bank}
    wallet["payment_method"] = "card_ua"

    await update.message.reply_text(
        f"{get_text('wallet_card_success', user_id)}\n\n<b>Card (UA):</b>\nNumber: {context.user_data['card_ua']}\nBank: {bank}",
        parse_mode='HTML'
    )
    if 'card_ua' in context.user_data:
        del context.user_data['card_ua']
    return await wallet_menu(update, context)

async def wallet_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    wallet["payment_method"] = "stars"

    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("wallet_stars_updated", user_id),
        parse_mode='HTML'
    )
    return await wallet_menu(update, context)

# ============================================================
# 11. РЕФЕРАЛЬНАЯ КНОПКА
# ============================================================
async def ref_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    ref_code = f"ref_{user_id}"
    link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
    refs = len(referrals.get(user_id, []))
    earned = referral_earnings.get(user_id, 0.0)

    text = get_text("ref_title", user_id,
                    link=link,
                    refs=refs,
                    earned=earned,
                    percent=REFERRAL_PERCENT)
    keyboard = [[InlineKeyboardButton(get_text("btn_back", user_id), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ============================================================
# 12. СМЕНА ЯЗЫКА
# ============================================================
async def lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    text = get_text("lang_title", user_id)
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(get_text("btn_back", user_id), callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = query.data.split('_')[1]
    user_lang[user_id] = lang
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text("lang_changed", user_id, lang=LANGUAGES[lang]["name"]),
        parse_mode='HTML'
    )
    await show_main_menu(update, context)

# ============================================================
# 13. ТЕХПОДДЕРЖКА
# ============================================================
async def support_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    text = get_text("support_title", user_id)
    keyboard = [[InlineKeyboardButton(get_text("btn_back", user_id), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

# ============================================================
# 14. ГЛАВНЫЙ ОБРАБОТЧИК КНОПОК
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if data == 'create_deal':
        await create_deal_start(update, context)
        return
    elif data == 'wallet':
        await wallet_menu(update, context)
        return
    elif data == 'ref':
        await ref_button(update, context)
        return
    elif data == 'lang':
        await lang_menu(update, context)
        return
    elif data == 'support':
        await support_button(update, context)
        return
    elif data.startswith('lang_'):
        await set_lang(update, context)
        return

    await query.message.delete()

    if data == 'admin_panel':
        if not is_admin(user_id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Нет доступа.")
            return
        text = get_text("admin_panel", user_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    elif data == 'back_to_menu':
        await show_main_menu(update, context)
    elif data.startswith('cancel_deal_'):
        deal_id = int(data.split('_')[2])
        deal = deals.get(deal_id)
        if deal and deal['status'] == 'active':
            deal['status'] = 'canceled'
            if deal['creator'] in user_deals:
                user_deals[deal['creator']] = [d for d in user_deals[deal['creator']] if d != deal_id]
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text("deal_canceled", user_id))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text("deal_not_found", user_id))
        await show_main_menu(update, context)
    elif data.startswith('confirm_deal_'):
        deal_id = int(data.split('_')[2])
        deal = deals.get(deal_id)
        if deal and deal['status'] == 'active':
            deal['status'] = 'completed'
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text("deal_confirmed", user_id))
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text("deal_not_found", user_id))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда.")

# ============================================================
# 15. ОБЫЧНЫЕ КОМАНДЫ
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(get_text("help_text", user_id), parse_mode='HTML')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Используйте /start для главного меню.")

# ============================================================
# 16. АДМИН-КОМАНДЫ
# ============================================================
async def wrfas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    text = get_text("admin_panel", user_id) + f"\n\n<b>Владельцы:</b> {', '.join(str(uid) for uid in ADMIN_IDS)}"
    msg = await update.message.reply_text(text, parse_mode='HTML')
    try:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        logger.warning(f"Не удалось закрепить: {e}")

async def buyslnft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Укажите ID сделки: /buyslnft <ID>")
        return
    try:
        deal_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ ID должен быть числом.")
        return
    deal = deals.get(deal_id)
    if not deal:
        await update.message.reply_text(f"❌ Сделка с ID {deal_id} не найдена.")
        return
    if deal['status'] == 'completed':
        await update.message.reply_text(f"ℹ️ Сделка {deal_id} уже завершена.")
        return
    seller_id = deal['creator']
    amount = deal['amount']
    add_balance(seller_id, amount)
    deal['status'] = 'completed'
    await update.message.reply_text(
        f"{EMOJI_TAGS['check']} Сделка {deal_id} завершена.\n"
        f"Продавцу (ID: {seller_id}) начислено {amount} STARS."
    )

async def vidach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Использование: /vidach <user_id> <сумма>")
        return
    try:
        target_id = int(args[0])
        amount = float(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Некорректный формат.")
        return
    if amount <= 0:
        await update.message.reply_text("⚠️ Сумма должна быть положительной.")
        return
    add_balance(target_id, amount)
    await update.message.reply_text(
        f"{EMOJI_TAGS['money']} Баланс пользователя {target_id} пополнен на {amount:.2f} STARS.\n"
        f"Текущий баланс: {get_balance(target_id):.2f} STARS."
    )

async def sdelkibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Укажите ID пользователя: /sdelkibo <user_id>")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ ID должен быть числом.")
        return
    descriptions = ["Покупка NFT", "Продажа NFT", "Обмен токенов", "Продажа NFT (фиктивная)"]
    for i, desc in enumerate(descriptions):
        if i % 2 == 0:
            creator = target_id
        else:
            creator = ADMIN_IDS[0]
        amount = round(10 + (hash(desc + str(i)) % 100), 2)
        create_deal(creator, amount, description=desc)
    await update.message.reply_text(
        f"{EMOJI_TAGS['briefcase']} Для пользователя {target_id} создано 4 фиктивные сделки."
    )

# ============================================================
# 17. ЗАПУСК
# ============================================================
def main():
    application = Application.builder().token(TOKEN).build()

    conv_deal = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_deal_start, pattern='^create_deal$')],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_deal_amount)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_deal_description)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_dialog),
            CallbackQueryHandler(cancel_dialog, pattern='^cancel_dialog$'),
            CallbackQueryHandler(button_handler, pattern='^back_to_menu$'),
        ],
        allow_reentry=True,
    )
    application.add_handler(conv_deal)

    conv_wallet = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(wallet_menu, pattern='^wallet$'),
            CallbackQueryHandler(wallet_ton_start, pattern='^wallet_ton$'),
            CallbackQueryHandler(wallet_sbp_start, pattern='^wallet_sbp$'),
            CallbackQueryHandler(wallet_card_rf_start, pattern='^wallet_card_rf$'),
            CallbackQueryHandler(wallet_card_ua_start, pattern='^wallet_card_ua$'),
            CallbackQueryHandler(wallet_stars, pattern='^wallet_stars$'),
        ],
        states={
            WALLET_MAIN: [
                CallbackQueryHandler(wallet_ton_start, pattern='^wallet_ton$'),
                CallbackQueryHandler(wallet_sbp_start, pattern='^wallet_sbp$'),
                CallbackQueryHandler(wallet_card_rf_start, pattern='^wallet_card_rf$'),
                CallbackQueryHandler(wallet_card_ua_start, pattern='^wallet_card_ua$'),
                CallbackQueryHandler(wallet_stars, pattern='^wallet_stars$'),
                CallbackQueryHandler(button_handler, pattern='^back_to_menu$'),
            ],
            WALLET_TON_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_ton_input)],
            WALLET_SBP_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_sbp_phone)],
            WALLET_SBP_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_sbp_bank)],
            WALLET_CARD_RF_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_card_rf_input)],
            WALLET_CARD_RF_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_card_rf_bank)],
            WALLET_CARD_UA_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_card_ua_input)],
            WALLET_CARD_UA_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_card_ua_bank)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_dialog),
            CallbackQueryHandler(button_handler, pattern='^back_to_menu$'),
        ],
        allow_reentry=True,
    )
    application.add_handler(conv_wallet)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wrfas", wrfas))
    application.add_handler(CommandHandler("buyslnft", buyslnft))
    application.add_handler(CommandHandler("vidach", vidach))
    application.add_handler(CommandHandler("sdelkibo", sdelkibo))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

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
