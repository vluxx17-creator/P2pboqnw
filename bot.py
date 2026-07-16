import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

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
    "link": '<tg-emoji emoji-id="5206607081334906820">🔗</tg-emoji>'
}
SYMBOLS = {k: v.split('>')[1].split('<')[0] for k, v in EMOJI_TAGS.items()}

# ============================================================
# 4. ХРАНИЛИЩА ДАННЫХ
# ============================================================
balances = {}
deals = {}
user_deals = {}
deal_counter = 0

# ============================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_balance(user_id: int) -> float:
    return balances.get(user_id, 0.0)

def add_balance(user_id: int, amount: float) -> None:
    balances[user_id] = get_balance(user_id) + amount

def create_deal(buyer: int, seller: int, amount: float, description: str = "") -> int:
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

# ============================================================
# 6. КОМАНДА /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        f"{EMOJI_TAGS['rocket']} <b>Добро пожаловать в ELF OTC – надёжный P2P-гарант</b>\n\n"
        f"<b>Покупайте и продавайте всё, что угодно – безопасно!</b>\n"
        f"От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
        f"• Удобное управление кошельками\n"
        f"• Реферальная система\n\n"
        f"<b>Как пользоваться?</b>\n"
        f"Ознакомьтесь с инструкцией —\n"
        f"<a href='{GUIDE_URL}'>Подробный гайд по использованию</a>\n\n"
        f"Выберите нужный раздел ниже:"
    )
    keyboard = [
        [InlineKeyboardButton(f"{SYMBOLS['wallet']} Добавить/изменить кошелёк", callback_data='wallet')],
        [InlineKeyboardButton(f"{SYMBOLS['money']} Создать сделку", callback_data='create_deal')],
        [InlineKeyboardButton(f"{SYMBOLS['link']} Реферальная ссылка", callback_data='ref')],
        [InlineKeyboardButton(f"{SYMBOLS['globe']} Сменить язык", callback_data='lang')],
        [InlineKeyboardButton(f"{SYMBOLS['heart']} Поддержка", callback_data='support')],
    ]
    if is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton(f"{SYMBOLS['star']} Админ-панель", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=BANNER_URL,
        caption=caption,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ============================================================
# 7. ОБРАБОТЧИК ИНЛАЙН-КНОПОК
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if data == 'wallet':
        text = f"{EMOJI_TAGS['wallet']} <b>Управление кошельками</b>\n\nФункция в разработке."
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'create_deal':
        text = (
            f"{EMOJI_TAGS['money']} <b>Создание сделки</b>\n\n"
            f"Используйте команды:\n"
            f"/buy &lt;сумма&gt; &lt;валюта&gt; – вы покупатель\n"
            f"/sell &lt;сумма&gt; &lt;валюта&gt; – вы продавец"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'ref':
        text = (
            f"{EMOJI_TAGS['link']} <b>Реферальная ссылка</b>\n\n"
            f"<code>https://t.me/YourBotBot?start=ref_{user_id}</code>"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'lang':
        text = f"{EMOJI_TAGS['globe']} <b>Смена языка</b>\n\nДоступен русский."
        await query.edit_message_text(text, parse_mode='HTML')
    elif data == 'support':
        text = f"{EMOJI_TAGS['heart']} <b>Поддержка</b>\n\n<a href='{SUPPORT_URL}'>Форма связи</a>"
        await query.edit_message_text(text, parse_mode='HTML', disable_web_page_preview=True)
    elif data == 'admin_panel':
        if not is_admin(user_id):
            await query.edit_message_text("⛔ Нет доступа.")
            return
        text = (
            f"{EMOJI_TAGS['star']} <b>Админ-панель</b>\n\n"
            f"/wrfas – список команд\n"
            f"/buyslnft &lt;ID&gt; – завершить сделку\n"
            f"/vidach &lt;user_id&gt; &lt;сумма&gt; – пополнить баланс\n"
            f"/sdelkibo &lt;user_id&gt; – накрутить сделки"
        )
        await query.edit_message_text(text, parse_mode='HTML')
    else:
        await query.edit_message_text("Неизвестная команда.")

# ============================================================
# 8. ОБЫЧНЫЕ КОМАНДЫ
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{EMOJI_TAGS['pin']} <b>Доступные команды:</b>\n"
        f"/start – главное меню\n"
        f"/help – эта справка\n"
        f"/buy &lt;сумма&gt; &lt;валюта&gt; – создать заявку на покупку\n"
        f"/sell &lt;сумма&gt; &lt;валюта&gt; – создать заявку на продажу"
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith('/buy'):
        args = text.split()
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите сумму и валюту, например: /buy 100 USDT")
            return
        try:
            amount = float(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ Сумма должна быть числом.")
            return
        currency = args[2] if len(args) > 2 else "USDT"
        buyer = update.effective_user.id
        seller = ADMIN_IDS[0]
        deal_id = create_deal(buyer, seller, amount, description=f"Покупка {amount} {currency}")
        await update.message.reply_text(
            f"{EMOJI_TAGS['money2']} Заявка на покупку создана!\nID сделки: {deal_id}"
        )
    elif text.startswith('/sell'):
        args = text.split()
        if len(args) < 2:
            await update.message.reply_text("⚠️ Укажите сумму и валюту, например: /sell 100 USDT")
            return
        try:
            amount = float(args[1])
        except ValueError:
            await update.message.reply_text("⚠️ Сумма должна быть числом.")
            return
        currency = args[2] if len(args) > 2 else "USDT"
        buyer = ADMIN_IDS[0]
        seller = update.effective_user.id
        deal_id = create_deal(buyer, seller, amount, description=f"Продажа {amount} {currency}")
        await update.message.reply_text(
            f"{EMOJI_TAGS['coin2']} Заявка на продажу создана!\nID сделки: {deal_id}"
        )
    else:
        await update.message.reply_text(f"{EMOJI_TAGS['pin']} Используйте /start для главного меню.")

# ============================================================
# 9. АДМИН-КОМАНДЫ
# ============================================================
async def wrfas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    text = (
        f"{EMOJI_TAGS['star']} <b>Список админ-команд:</b>\n\n"
        f"🔹 <code>/wrfas</code> – показать этот список и закрепить сообщение.\n"
        f"🔹 <code>/buyslnft &lt;ID_сделки&gt;</code> – завершить активную сделку. Продавцу начисляются средства.\n"
        f"🔹 <code>/vidach &lt;user_id&gt; &lt;сумма&gt;</code> – пополнить баланс указанного пользователя.\n"
        f"🔹 <code>/sdelkibo &lt;user_id&gt;</code> – создать несколько фиктивных сделок для демонстрации.\n\n"
        f"<b>Владельцы:</b> {', '.join(str(uid) for uid in ADMIN_IDS)}"
    )
    msg = await update.message.reply_text(text, parse_mode='HTML')
    try:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        logger.warning(f"Не удалось закрепить сообщение: {e}")

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
    seller_id = deal['seller']
    amount = deal['amount']
    add_balance(seller_id, amount)
    deal['status'] = 'completed'
    await update.message.reply_text(
        f"{EMOJI_TAGS['check']} Сделка {deal_id} завершена.\n"
        f"Продавцу (ID: {seller_id}) начислено {amount} USDT."
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
        f"{EMOJI_TAGS['money']} Баланс пользователя {target_id} пополнен на {amount:.2f} USDT.\n"
        f"Текущий баланс: {get_balance(target_id):.2f} USDT."
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
        if i == 3:
            buyer = ADMIN_IDS[0]
            seller = target_id
        else:
            buyer = target_id
            seller = ADMIN_IDS[0]
        amount = round(10 + (hash(desc + str(i)) % 100), 2)
        create_deal(buyer, seller, amount, description=desc)
    await update.message.reply_text(
        f"{EMOJI_TAGS['briefcase']} Для пользователя {target_id} создано 4 фиктивные сделки."
    )

# ============================================================
# 10. FLASK-ПРИЛОЖЕНИЕ
# ============================================================
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return 'ok', 200

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

# ============================================================
# 11. ЗАПУСК БОТА (исправленный)
# ============================================================
if __name__ == '__main__':
    # Создаём экземпляр Application
    application = Application.builder().token(TOKEN).build()

    # Регистрируем все обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wrfas", wrfas))
    application.add_handler(CommandHandler("buyslnft", buyslnft))
    application.add_handler(CommandHandler("vidach", vidach))
    application.add_handler(CommandHandler("sdelkibo", sdelkibo))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Настраиваем порт и вебхук
    port = int(os.environ.get("PORT", 10000))
    external_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

    async def setup_webhook():
        if external_url:
            webhook_url = f"https://{external_url}/webhook"
            logger.info(f"Установка вебхука: {webhook_url}")
            await application.bot.set_webhook(url=webhook_url)
        else:
            logger.warning("Переменная RENDER_EXTERNAL_HOSTNAME не найдена. Вебхук не установлен.")

    # Устанавливаем вебхук
    asyncio.run(setup_webhook())

    # Запускаем Flask-сервер
    app.run(host="0.0.0.0", port=port)
