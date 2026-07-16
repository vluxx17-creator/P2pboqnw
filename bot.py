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
# 4. СОСТОЯНИЯ ДЛЯ ДИАЛОГА
# ============================================================
AMOUNT, DESCRIPTION = range(2)

# ============================================================
# 5. ХРАНИЛИЩА
# ============================================================
balances = {}
deals = {}
user_deals = {}
deal_counter = 0
temp_deal_data = {}

# ============================================================
# 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
# 7. ГЛАВНОЕ МЕНЮ (ОТПРАВЛЯЕТ НОВОЕ СООБЩЕНИЕ С ФОТО)
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        code = context.args[0]
        if code.startswith("deal_"):
            deal = get_deal_by_code(code)
            if deal and deal["status"] == "active":
                await show_deal_to_buyer(update, context, deal)
                return
            else:
                await update.message.reply_text("❌ Сделка не найдена или уже завершена.")
                return

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

    # Если сообщение пришло из колбэка (возврат в меню) – удаляем старое и отправляем новое
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
        # Обычный /start
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=BANNER_URL,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def show_deal_to_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE, deal: dict):
    text = (
        f"{EMOJI_TAGS['money']} <b>Информация о сделке</b>\n\n"
        f"Сумма: <b>{deal['amount']} STARS</b>\n"
        f"Описание: {deal['description']}\n\n"
        f"Для подтверждения сделки нажмите кнопку ниже."
    )
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить сделку", callback_data=f"confirm_deal_{deal['id']}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_deal_{deal['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

# ============================================================
# 8. ДИАЛОГ СОЗДАНИЯ СДЕЛКИ
# ============================================================
async def create_deal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{EMOJI_TAGS['money']} <b>Создание сделки</b>\n\nВведите сумму STARS в формате:\n<code>2000</code>",
        parse_mode='HTML'
    )
    return AMOUNT

async def create_deal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Пожалуйста, введите корректное положительное число.")
        return AMOUNT

    user_id = update.effective_user.id
    temp_deal_data[user_id] = {"amount": amount}

    await update.message.reply_text(
        f"{EMOJI_TAGS['pen']} <b>Укажите, что вы предлагаете в этой сделке:</b>\n\n<i>Пример: 10 Кепок и Пене...</i>",
        parse_mode='HTML'
    )
    return DESCRIPTION

async def create_deal_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()
    if not description:
        await update.message.reply_text("⚠️ Описание не может быть пустым. Попробуйте ещё раз.")
        return DESCRIPTION

    user_id = update.effective_user.id
    data = temp_deal_data.get(user_id)
    if not data:
        await update.message.reply_text("❌ Что-то пошло не так. Начните заново через /start")
        return ConversationHandler.END

    amount = data["amount"]
    deal = create_deal(user_id, amount, description)

    text = (
        f"{EMOJI_TAGS['check']} <b>Сделка успешно создана!</b>\n\n"
        f"Сумма: <b>{int(amount)} STARS</b>\n\n"
        f"<b>Описание:</b>\n{description}\n\n"
        f"Ссылка для покупателя:\n<code>{deal['buyer_link']}</code>\n\n"
        f"<i>dev: @seinarukiro</i>\n<i>t.me/otcgifttq</i>"
    )
    keyboard = [
        [InlineKeyboardButton("❌ Отменить сделку", callback_data=f"cancel_deal_{deal['id']}")],
        [InlineKeyboardButton("↩️ Вернуться в меню", callback_data="back_to_menu")]
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
    await update.message.reply_text("❌ Создание сделки отменено.")
    await start(update, context)
    return ConversationHandler.END

# ============================================================
# 9. ОБРАБОТЧИК ИНЛАЙН-КНОПОК (ВСЕ КНОПКИ КРОМЕ CREATE_DEAL)
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    # Если это создание сделки – передаём в ConversationHandler
    if data == 'create_deal':
        await create_deal_start(update, context)
        return

    # Удаляем исходное сообщение (фото с кнопками)
    await query.message.delete()

    if data == 'wallet':
        text = f"{EMOJI_TAGS['wallet']} <b>Управление кошельками</b>\n\nФункция в разработке."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    elif data == 'ref':
        text = (
            f"{EMOJI_TAGS['link']} <b>Реферальная ссылка</b>\n\n"
            f"<code>https://t.me/{BOT_USERNAME}?start=ref_{user_id}</code>"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    elif data == 'lang':
        text = f"{EMOJI_TAGS['globe']} <b>Смена языка</b>\n\nДоступен русский."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    elif data == 'support':
        text = f"{EMOJI_TAGS['heart']} <b>Поддержка</b>\n\n<a href='{SUPPORT_URL}'>Форма связи</a>"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    elif data == 'admin_panel':
        if not is_admin(user_id):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Нет доступа.")
            return
        text = (
            f"{EMOJI_TAGS['star']} <b>Админ-панель</b>\n\n"
            f"/wrfas – список команд\n"
            f"/buyslnft &lt;ID&gt; – завершить сделку\n"
            f"/vidach &lt;user_id&gt; &lt;сумма&gt; – пополнить баланс\n"
            f"/sdelkibo &lt;user_id&gt; – накрутить сделки"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')
    elif data == 'back_to_menu':
        # Возвращаем главное меню (start обработает callback)
        await start(update, context)
    elif data.startswith('cancel_deal_'):
        deal_id = int(data.split('_')[2])
        deal = deals.get(deal_id)
        if deal and deal['status'] == 'active':
            deal['status'] = 'canceled'
            if deal['creator'] in user_deals:
                user_deals[deal['creator']] = [d for d in user_deals[deal['creator']] if d != deal_id]
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Сделка отменена.")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Сделка не найдена или уже неактивна.")
        await start(update, context)
    elif data.startswith('confirm_deal_'):
        deal_id = int(data.split('_')[2])
        deal = deals.get(deal_id)
        if deal and deal['status'] == 'active':
            deal['status'] = 'completed'
            await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Сделка подтверждена и завершена!")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Сделка не найдена или уже завершена.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда.")

# ============================================================
# 10. ОБЫЧНЫЕ КОМАНДЫ (СОВМЕСТИМОСТЬ)
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"{EMOJI_TAGS['pin']} <b>Доступные команды:</b>\n/start – главное меню\n/help – эта справка"
    await update.message.reply_text(text, parse_mode='HTML')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Этот обработчик не будет вызван, если активен ConversationHandler
    await update.message.reply_text("Используйте /start для главного меню.")

# ============================================================
# 11. АДМИН-КОМАНДЫ
# ============================================================
async def wrfas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    text = (
        f"{EMOJI_TAGS['star']} <b>Список админ-команд:</b>\n\n"
        f"🔹 <code>/wrfas</code> – показать этот список и закрепить сообщение.\n"
        f"🔹 <code>/buyslnft &lt;ID_сделки&gt;</code> – завершить сделку. Продавцу начисляются средства.\n"
        f"🔹 <code>/vidach &lt;user_id&gt; &lt;сумма&gt;</code> – пополнить баланс.\n"
        f"🔹 <code>/sdelkibo &lt;user_id&gt;</code> – создать фиктивные сделки.\n\n"
        f"<b>Владельцы:</b> {', '.join(str(uid) for uid in ADMIN_IDS)}"
    )
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
# 12. ЗАПУСК
# ============================================================
def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
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
    application.add_handler(conv_handler)

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
