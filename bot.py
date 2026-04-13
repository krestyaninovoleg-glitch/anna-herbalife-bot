import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Final

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN: Final[str] = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID: Final[str] = os.getenv("ADMIN_CHAT_ID", "")
SITE_LINK: Final[str] = "https://a-yakubenko.com"
WHATSAPP_LINK: Final[str] = "https://wa.me/97450146509?text=Здравствуйте!%20Хочу%20получить%20консультацию%20по%20Herbalife."
TELEGRAM_BOT_LINK: Final[str] = "https://t.me/anna_yakubenko_bot"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LEADS_FILE = DATA_DIR / "leads.csv"

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

(
    LEAD_NAME,
    LEAD_CONTACT,
    LEAD_GOAL,
    LEAD_COUNTRY,
    LEAD_NOTE,
) = range(5)

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["🌿 Продукты", "🎯 Подобрать программу"],
        ["💬 Консультация", "✨ Клуб ЗОЖ"],
        ["📦 Акция", "📝 Оставить заявку"],
        ["📲 WhatsApp", "🌐 Сайт"],
    ],
    resize_keyboard=True,
)

CONTACT_MENU = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 Отправить телефон", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

GOALS = {
    "weight": "Снижение веса",
    "energy": "Больше энергии",
    "routine": "Комфортный рацион",
    "muscle": "Белок и восстановление",
    "consult": "Нужна консультация",
}

PRODUCT_TEXT = (
    "<b>Популярные продукты Herbalife</b>\n\n"
    "🥤 <b>Formula 1</b>\n"
    "Флагманский коктейль для удобного сбалансированного рациона.\n\n"
    "💪 <b>Protein Drink Mix</b>\n"
    "Белковый напиток, который удобно добавлять в ежедневное меню.\n\n"
    "🧭 <b>Персональная программа</b>\n"
    "Подбор маршрута старта, сопровождение и поддержка."
)

PROMO_TEXT = (
    "🎁 <b>Спецпредложение</b>\n\n"
    "Оставьте заявку, и Анна поможет подобрать комфортный старт, "
    "формат сопровождения и удобный способ связи."
)

CLUB_TEXT = (
    "✨ <b>Клуб здорового образа жизни</b>\n\n"
    "Это формат поддержки, где удобно:\n"
    "• начать изменения без перегруза\n"
    "• получать мотивацию\n"
    "• двигаться в комфортном темпе\n"
    "• быть на связи в привычном мессенджере"
)

CONSULT_TEXT = (
    "💬 <b>Консультация</b>\n\n"
    "Напишите, какая у вас цель, и Анна поможет подобрать "
    "самый понятный и удобный маршрут старта."
)

def ensure_csv() -> None:
    if not LEADS_FILE.exists():
        with LEADS_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "created_at",
                "name",
                "contact",
                "goal",
                "country",
                "note",
                "telegram_id",
                "telegram_username",
                "telegram_name",
            ])

def save_lead(
    *,
    name: str,
    contact: str,
    goal: str,
    country: str,
    note: str,
    telegram_id: str,
    telegram_username: str,
    telegram_name: str,
) -> None:
    ensure_csv()
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            name,
            contact,
            goal,
            country,
            note,
            telegram_id,
            telegram_username,
            telegram_name,
        ])

def top_inline_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎯 Подобрать программу", callback_data="pick_program")],
            [InlineKeyboardButton("📝 Оставить заявку", callback_data="lead_start")],
            [InlineKeyboardButton("📲 WhatsApp", url=WHATSAPP_LINK)],
            [InlineKeyboardButton("🌐 Сайт", url=SITE_LINK)],
        ]
    )

def goals_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Снижение веса", callback_data="goal_weight")],
            [InlineKeyboardButton("Больше энергии", callback_data="goal_energy")],
            [InlineKeyboardButton("Комфортный рацион", callback_data="goal_routine")],
            [InlineKeyboardButton("Белок и восстановление", callback_data="goal_muscle")],
            [InlineKeyboardButton("Нужна консультация", callback_data="goal_consult")],
        ]
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Здравствуйте! Добро пожаловать 🌿\n\n"
        "Я PRO-бот Анны Якубенко.\n"
        "Помогу вам:\n"
        "• узнать о продуктах Herbalife\n"
        "• подобрать программу под цель\n"
        "• оставить заявку\n"
        "• быстро перейти в WhatsApp или на сайт\n\n"
        "Выберите, что вас интересует."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    await update.message.reply_text("Быстрый старт:", reply_markup=top_inline_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — главное меню\n"
        "/products — продукты\n"
        "/program — подбор программы\n"
        "/consult — консультация\n"
        "/club — клуб ЗОЖ\n"
        "/promo — акция\n"
        "/lead — оставить заявку\n"
        "/contact — контакты\n"
        "/export_leads — экспорт заявок",
        reply_markup=MAIN_MENU,
    )

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        PRODUCT_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=goals_inline(),
    )

async def consult(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        CONSULT_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=goals_inline(),
    )

async def club(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        CLUB_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=top_inline_menu(),
    )

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        PROMO_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=top_inline_menu(),
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Контакты Анны:\n"
        "📲 WhatsApp: +974 5014 6509\n"
        f"🤖 Бот: {TELEGRAM_BOT_LINK}\n"
        f"🌐 Сайт: {SITE_LINK}",
        reply_markup=top_inline_menu(),
    )

async def program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Выберите цель, и я подскажу удобный маршрут старта:",
        reply_markup=goals_inline(),
    )

async def lead_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Давайте оформим заявку.\n\nКак вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return LEAD_NAME

async def lead_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["lead_name"] = (update.effective_message.text or "").strip()
    await update.effective_message.reply_text(
        "Оставьте номер телефона, WhatsApp или @username Telegram.\n"
        "Можно просто отправить текстом или нажать кнопку ниже.",
        reply_markup=CONTACT_MENU,
    )
    return LEAD_CONTACT

async def lead_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_message.contact:
        contact_value = update.effective_message.contact.phone_number
    else:
        contact_value = (update.effective_message.text or "").strip()

    context.user_data["lead_contact"] = contact_value
    await update.effective_message.reply_text(
        "Какая у вас основная цель?\n"
        "Например: снижение веса, больше энергии, белок, консультация.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return LEAD_GOAL

async def lead_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["lead_goal"] = (update.effective_message.text or "").strip()
    await update.effective_message.reply_text(
        "Из какой вы страны?\nНапример: Казахстан, Россия, Катар.",
    )
    return LEAD_COUNTRY

async def lead_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["lead_country"] = (update.effective_message.text or "").strip()
    await update.effective_message.reply_text(
        "Добавьте комментарий, если хотите.\n"
        "Например: когда удобно связаться или что именно интересно.\n\n"
        "Если комментария нет, напишите: нет",
    )
    return LEAD_NOTE

async def lead_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    note = (update.effective_message.text or "").strip()
    user = update.effective_user

    lead = {
        "name": context.user_data.get("lead_name", "-"),
        "contact": context.user_data.get("lead_contact", "-"),
        "goal": context.user_data.get("lead_goal", "-"),
        "country": context.user_data.get("lead_country", "-"),
        "note": note,
        "telegram_id": str(user.id) if user else "",
        "telegram_username": f"@{user.username}" if user and user.username else "",
        "telegram_name": user.full_name if user else "",
    }

    save_lead(**lead)

    admin_text = (
        "🟢 <b>Новая заявка с PRO-бота</b>\n\n"
        f"<b>Имя:</b> {lead['name']}\n"
        f"<b>Контакт:</b> {lead['contact']}\n"
        f"<b>Цель:</b> {lead['goal']}\n"
        f"<b>Страна:</b> {lead['country']}\n"
        f"<b>Комментарий:</b> {lead['note']}\n"
        f"<b>Telegram:</b> {lead['telegram_username'] or 'без username'}\n"
        f"<b>ID:</b> {lead['telegram_id']}"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            logger.exception("Не удалось отправить заявку администратору.")

    await update.effective_message.reply_text(
        "Спасибо! Заявка сохранена ✅\n"
        "Анна свяжется с вами в ближайшее время.",
        reply_markup=MAIN_MENU,
    )
    await update.effective_message.reply_text(
        "Пока ждёте ответ, можете сразу перейти в WhatsApp:",
        reply_markup=top_inline_menu(),
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Заявка отменена.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or str(user.id) != str(ADMIN_CHAT_ID):
        await update.effective_message.reply_text("Эта команда доступна только администратору.")
        return

    ensure_csv()
    with LEADS_FILE.open("rb") as f:
        await update.effective_message.reply_document(
            document=f,
            filename="leads.csv",
            caption="Экспорт заявок",
        )

async def handle_goal_pick(update: Update, context: ContextTypes.DEFAULT_TYPE, goal_key: str) -> None:
    goal_title = GOALS.get(goal_key, "Консультация")
    text = (
        f"🎯 <b>Цель:</b> {goal_title}\n\n"
        "Следующий шаг:\n"
        "1. Получить краткую консультацию\n"
        "2. Подобрать удобный старт\n"
        "3. Перейти в WhatsApp или оставить заявку"
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=top_inline_menu(),
    )

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if data == "pick_program":
        await query.message.reply_text(
            "Выберите цель, и я помогу с подбором:",
            reply_markup=goals_inline(),
        )
        return None
    if data == "lead_start":
        await query.message.reply_text("Давайте оформим заявку.\n\nКак вас зовут?")
        return LEAD_NAME
    if data.startswith("goal_"):
        goal_key = data.replace("goal_", "", 1)
        await handle_goal_pick(update, context, goal_key)
        return None
    return None

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip().lower()

    if text == "🌿 продукты":
        await products(update, context)
    elif text == "🎯 подобрать программу":
        await program(update, context)
    elif text == "💬 консультация":
        await consult(update, context)
    elif text == "✨ клуб зож":
        await club(update, context)
    elif text == "📦 акция":
        await promo(update, context)
    elif text == "📝 оставить заявку":
        await lead_start(update, context)
    elif text == "📲 whatsapp":
        await update.effective_message.reply_text(
            "Быстрый переход в WhatsApp:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Открыть WhatsApp", url=WHATSAPP_LINK)]]
            ),
        )
    elif text == "🌐 сайт":
        await update.effective_message.reply_text(
            "Открыть сайт:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Перейти на сайт", url=SITE_LINK)]]
            ),
        )
    else:
        await update.effective_message.reply_text(
            "Выберите кнопку в меню или используйте /start",
            reply_markup=MAIN_MENU,
        )

def validate() -> None:
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN.")
    ensure_csv()

def main() -> None:
    validate()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("lead", lead_start),
            CallbackQueryHandler(callback_router, pattern="^lead_start$"),
            MessageHandler(filters.Regex("^📝 Оставить заявку$"), lead_start),
        ],
        states={
            LEAD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_name)],
            LEAD_CONTACT: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, lead_contact)],
            LEAD_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_goal)],
            LEAD_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_country)],
            LEAD_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_note)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("consult", consult))
    app.add_handler(CommandHandler("club", club))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("program", program))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("export_leads", admin_export))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    logger.info("PRO bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
