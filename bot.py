import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ---------- ЛОГИРОВАНИЕ ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- КОНФИГУРАЦИЯ ----------
TOKEN = "8578762350:AAFrd1SgZzm7IvELjcwrj6anShyzHeZlCws"
ADMIN_IDS = [8400055743, 8297446667]          # владельцы / админы
BANNER_URL = "https://i.ibb.co/7dTv2VP4/IMG-1367.jpg"
SUPPORT_URL = "https://forms.gle/4kN2r57SJiPrxBjf9"

# ---------- ПРЕМИУМ-ЭМОДЗИ (HTML-теги) ----------
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
    "users": '<tg-emoji emoji-id="5958460691550572213">👥</tg-emoji>'
}
# Обычные символы для кнопок (извлекаем из тегов)
SYMBOLS = {k: v.split('>')[1].split('<')[0] for k, v in EMOJI_TAGS.items()}

# ---------- ХРАНИЛИЩА (В ПАМЯТИ) ----------
balances = {}          # user_id -> float
deals = {}             # deal_id -> {buyer, seller, amount, status, description}
user_deals = {}        # user_id -> list of deal_ids
deal_counter = 0

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_balance(user_id: int) -> float:
    return balances.get(user_id, 0.0)

def add_balance(user_id: int, amount: float):
    balances[user_id] = get_balance(user_id) + amount

def create_deal(buyer: int, seller: int, amount: float, description: str = ""):
    global deal_counter
    deal_counter += 1
    deal_id = deal_counter
    deals[deal_id] = {
        "buyer": buyer,
        "seller": seller,
        "amount": amount,
        "status": "active",
        "description": description
    }
    user_deals.setdefault(buyer, []).append(deal_id)
    user_deals.setdefault(seller, []).append(deal_id)
    return deal_id

# ---------- ОБРАБОТЧИКИ КОМАНД ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню с баннером."""
    caption = (
        f"{EMOJI_TAGS['rocket']} <b>Добро пожаловать в OTC/P2P бот!</b>\n\n"
        f"Здесь вы можете безопасно покупать и продавать цифровые активы.\n"
        f"{EMOJI_TAGS['shield']} Все сделки защищены арбитражем.\n\n"
        f"Используйте кнопки ниже для навигации."
    )
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=BANNER_URL,
        caption=caption,
        parse_mode='HTML'
    )
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню с инлайн-кнопками."""
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(f"{SYMBOLS['money']} Купить", callback_data='buy')],
        [InlineKeyboardButton(f"{SYMBOLS['coin']} Продать", callback_data='sell')],
        [InlineKeyboardButton(f"{SYMBOLS['receipt']} Мои сделки", callback_data='my_deals')],
        [InlineKeyboardButton(f"{SYMBOLS['card']} Баланс", callback_data='balance')],
        [InlineKeyboardButton(f"{SYMBOLS['heart']} Поддержка", callback_data='support')],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton(f"{SYMBOLS['star']} Админ-панель", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{EMOJI_TAGS['globe']} <b>Главное меню</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if data == 'buy':
        text = (
            f"{EMOJI_TAGS['money']} <b>Покупка USDT</b>\n\n"
            f"Курс: 1 USDT = 1.00 USD\n"
            f"Минимальная сумма: 10 USDT\n"
            f"Максимальная: 1000 USDT\n\n"
            f"Чтобы создать заявку, отправьте команду:\n"
            f"/buy &lt;сумма&gt; &lt;валюта&gt; (например: /buy 100 RUB)"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'sell':
        text = (
            f"{EMOJI_TAGS['coin']} <b>Продажа USDT</b>\n\n"
            f"Курс: 1 USDT = 1.00 USD\n"
            f"Минимальная сумма: 10 USDT\n"
            f"Максимальная: 1000 USDT\n\n"
            f"Чтобы создать заявку, отправьте команду:\n"
            f"/sell &lt;сумма&gt; &lt;валюта&gt; (например: /sell 100 RUB)"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'my_deals':
        deals_list = user_deals.get(user_id, [])
        if not deals_list:
            text = f"{EMOJI_TAGS['receipt']} У вас нет активных сделок."
        else:
            text = f"{EMOJI_TAGS['receipt']} <b>Ваши сделки:</b>\n"
            for d_id in deals_list:
                deal = deals.get(d_id)
                if deal:
                    status = "✅ Завершена" if deal['status'] == 'completed' else "🔄 Активна"
                    text += f"\n🔹 ID: {d_id} | {deal['description']}\n   Сумма: {deal['amount']} USDT | Статус: {status}\n"
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'balance':
        bal = get_balance(user_id)
        text = f"{EMOJI_TAGS['card']} <b>Ваш баланс:</b> {bal:.2f} USDT"
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'support':
        text = (
            f"{EMOJI_TAGS['heart']} <b>Техническая поддержка</b>\n\n"
            f"Для связи с нами заполните форму:\n"
            f"<a href='{SUPPORT_URL}'>Нажмите здесь</a>"
        )
        await query.edit_message_text(text, parse_mode='HTML', disable_web_page_preview=True)
    elif data == 'admin_panel':
        if not is_admin(user_id):
            await query.edit_message_text("⛔ У вас нет доступа к админ-панели.")
            return
        text = (
            f"{EMOJI_TAGS['star']} <b>Админ-панель</b>\n\n"
            f"Доступные команды (вводите вручную):\n"
            f"/wrfas - список админ-команд\n"
            f"/buyslnft &lt;ID_сделки&gt; - завершить сделку\n"
            f"/vidach &lt;user_id&gt; &lt;сумма&gt; - пополнить баланс\n"
            f"/sdelkibo &lt;user_id&gt; - накрутить сделки\n\n"
            f"Владельцы: {', '.join(str(uid) for uid in ADMIN_IDS)}"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    else:
        await query.edit_message_text("Неизвестная команда.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам."""
    text = (
        f"{EMOJI_TAGS['pin']} <b>Доступные команды:</b>\n"
        f"/start - главное меню\n"
        f"/help - эта справка\n"
        f"/buy &lt;сумма&gt; &lt;валюта&gt; - создать заявку на покупку\n"
        f"/sell &lt;сумма&gt; &lt;валюта&gt; - создать заявку на продажу\n"
        f"Для администраторов:\n"
        f"/wrfas - список админ-команд"
    )
    await update.message.reply_text(text, parse_mode='HTML')

# ---------- АДМИН-КОМАНДЫ ----------
async def wrfas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список админ-команд с закреплением сообщения."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    text = (
        f"{EMOJI_TAGS['star']} <b>Список админ-команд:</b>\n\n"
        f"🔹 <code>/wrfas</code> – показать этот список и закрепить сообщение.\n"
        f"🔹 <code>/buyslnft &lt;ID_сделки&gt;</code> – завершить активную сделку. Продавцу начисляются средства.\n"
        f"🔹 <code>/vidach &lt;user_id&gt; &lt;сумма&gt;</code> – пополнить баланс указанного пользователя.\n"
        f"🔹 <code>/sdelkibo &lt;user_id&gt;</code> – создать несколько фиктивных сделок для пользователя (для демонстрации).\n\n"
        f"<b>Владельцы бота:</b> {', '.join(str(uid) for uid in ADMIN_IDS)}"
    )

    msg = await update.message.reply_text(text, parse_mode='HTML')
    # Закрепляем сообщение (если чат позволяет)
    try:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        logger.warning(f"Не удалось закрепить сообщение: {e}")

async def buyslnft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить сделку и начислить средства продавцу."""
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

    seller_id = deal['seller']
    amount = deal['amount']
    add_balance(seller_id, amount)
    deal['status'] = 'completed'

    await update.message.reply_text(
        f"{EMOJI_TAGS['check']} Сделка {deal_id} завершена.\n"
        f"Продавцу (ID: {seller_id}) начислено {amount} USDT."
    )

async def vidach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пополнить баланс пользователя."""
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
        await update.message.reply_text("⚠️ Некорректный формат. user_id – число, сумма – число.")
        return

    if amount <= 0:
        await update.message.reply_text("⚠️ Сумма должна быть положительной.")
        return

    add_balance(target_id, amount)
    await update.message.reply_text(
        f"{EMOJI_TAGS['money']} Баланс пользователя {target_id} пополнен на {amount:.2f} USDT.\n"
        f"Текущий баланс: {get_balance(target_id):.2f} USDT."
    )

async def sdelkibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Накрутка фиктивных сделок для пользователя."""
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

    # Создаём 4 фиктивные сделки с разными описаниями
    descriptions = ["Покупка USDT", "Продажа BTC", "Обмен ETH", "Продажа USDT (фиктивная)"]
    for i, desc in enumerate(descriptions):
        if i == 3:  # последняя – target_id продавец
            buyer = ADMIN_IDS[0]
            seller = target_id
        else:
            buyer = target_id
            seller = ADMIN_IDS[0]
        amount = round(10 + (hash(desc + str(i)) % 100), 2)
        create_deal(buyer, seller, amount, description=desc)

    await update.message.reply_text(
        f"{EMOJI_TAGS['briefcase']} Для пользователя {target_id} создано 4 фиктивные сделки.\n"
        f"Используйте /my_deals или посмотрите в меню 'Мои сделки'."
    )

# ---------- ОБРАБОТЧИК ТЕКСТА ДЛЯ /buy И /sell ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команды /buy и /sell, создавая сделки."""
    text = update.message.text
    if text.startswith('/buy'):
        args = text.split()
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите сумму и валюту, например: /buy 100 RUB")
            return
        try:
            amount = float(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ Сумма должна быть числом.")
            return
        currency = args[2] if len(args) > 2 else "USD"
        buyer = update.effective_user.id
        seller = ADMIN_IDS[0]  # продавец – первый админ
        deal_id = create_deal(buyer, seller, amount, description=f"Покупка {amount} USDT за {currency}")
        await update.message.reply_text(
            f"{EMOJI_TAGS['money2']} Заявка на покупку создана!\n"
            f"ID сделки: {deal_id}\n"
            f"Сумма: {amount} USDT\n"
            f"Валюта: {currency}\n"
            f"Статус: ожидает подтверждения."
        )
    elif text.startswith('/sell'):
        args = text.split()
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите сумму и валюту, например: /sell 100 RUB")
            return
        try:
            amount = float(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ Сумма должна быть числом.")
            return
        currency = args[2] if len(args) > 2 else "USD"
        buyer = ADMIN_IDS[0]
        seller = update.effective_user.id
        deal_id = create_deal(buyer, seller, amount, description=f"Продажа {amount} USDT за {currency}")
        await update.message.reply_text(
            f"{EMOJI_TAGS['coin2']} Заявка на продажу создана!\n"
            f"ID сделки: {deal_id}\n"
            f"Сумма: {amount} USDT\n"
            f"Валюта: {currency}\n"
            f"Статус: ожидает подтверждения."
        )
    else:
        await update.message.reply_text(
            f"{EMOJI_TAGS['pin']} Используйте /start для главного меню или /help для справки."
        )

# ---------- ЗАПУСК БОТА (LONG POLLING) ----------
def main():
    """Инициализация и запуск бота."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wrfas", wrfas))
    application.add_handler(CommandHandler("buyslnft", buyslnft))
    application.add_handler(CommandHandler("vidach", vidach))
    application.add_handler(CommandHandler("sdelkibo", sdelkibo))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен и работает в режиме long polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
