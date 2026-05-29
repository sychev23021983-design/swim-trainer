import os, asyncio, logging, json
from datetime import datetime
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, filters, ContextTypes)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

DAY_RU = {"mon":"пн","tue":"вт","wed":"ср","thu":"чт","fri":"пт","sat":"сб","sun":"вс"}
DAY_EN = {"Monday":"mon","Tuesday":"tue","Wednesday":"wed","Thursday":"thu",
          "Friday":"fri","Saturday":"sat","Sunday":"sun"}

# ---- State for awaiting reps input ----
pending_input: dict = {}

async def api_get(path: str):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BACKEND_URL}{path}")
        return r.json()

async def api_post(path: str, data: dict):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BACKEND_URL}{path}", json=data)
        return r.json()

# ---- Build today message ----
async def build_today_message():
    tasks = await api_get("/api/today")
    summary = await api_get("/api/rewards/summary")
    today = datetime.now().strftime("%d.%m.%Y")
    if not tasks:
        return f"На сегодня ({today}) тренировок нет. Отдыхай!", None
    total_reward = sum(t["reward_usd"] for t in tasks if not t["completed_today"])
    pending = [t for t in tasks if not t["completed_today"]]
    done    = [t for t in tasks if t["completed_today"]]
    lines = [f"Время стать на 1% лучше!\n{today}\n"]
    if pending:
        lines.append("Сегодня:")
        for t in pending:
            reps_str = f"{t['sets']}×{t['reps']}" if t.get("reps") else f"{t['sets']} подх."
            dur_str  = f"{t['duration_sec']}сек" if t.get("duration_sec") else ""
            lines.append(f"• {t['title']} — {reps_str}{' '+dur_str if dur_str else ''} (+${t['reward_usd']:.2f})")
    if done:
        lines.append(f"\nВыполнено сегодня ({len(done)}):")
        for t in done:
            lines.append(f"✓ {t['title']}")
    lines.append(f"\nНаграда за все: ${total_reward:.2f}")
    lines.append(f"Баланс: ${summary['balance']:.2f}")
    if summary["streak_days"] > 1:
        lines.append(f"Серия: {summary['streak_days']} дней подряд!")
    msg = "\n".join(lines)
    if not pending:
        return msg, None
    buttons = []
    for t in pending:
        row = []
        if t["input_type"] == "done":
            row.append(InlineKeyboardButton(f"✓ {t['title'][:25]}", callback_data=f"done:{t['exercise_id']}"))
        else:
            row.append(InlineKeyboardButton(f"Ввести: {t['title'][:20]}", callback_data=f"input:{t['exercise_id']}:{t.get('reps',0)}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Показать все задания", callback_data="show_all")])
    return msg, InlineKeyboardMarkup(buttons)

# ---- Scheduler: send daily notifications ----
async def send_daily(app: Application):
    if not CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID not set")
        return
    try:
        tasks = await api_get("/api/today")
        if not tasks: return
        msg, kb = await build_today_message()
        await app.bot.send_message(chat_id=CHAT_ID, text=msg, reply_markup=kb)
        log.info(f"Sent daily notification: {len(tasks)} tasks")
    except Exception as e:
        log.error(f"send_daily error: {e}")

# ---- Schedule APScheduler jobs from backend ----
async def reload_schedules(scheduler: AsyncIOScheduler, app: Application):
    for job in scheduler.get_jobs():
        if job.id.startswith("notify_"):
            job.remove()
    try:
        schedules = await api_get("/api/schedules")
        times_seen = set()
        for s in schedules:
            if not s.get("active"): continue
            t = s.get("notify_time","17:00")
            if t in times_seen: continue
            times_seen.add(t)
            h, m = map(int, t.split(":"))
            scheduler.add_job(send_daily, "cron", hour=h, minute=m,
                              id=f"notify_{t.replace(':','')}", args=[app])
            log.info(f"Scheduled notification at {t}")
    except Exception as e:
        log.error(f"reload_schedules error: {e}")

# ---- Handlers ----
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, kb = await build_today_message()
    await update.message.reply_text(msg, reply_markup=kb)

async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, kb = await build_today_message()
    await update.message.reply_text(msg, reply_markup=kb)

async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    summary = await api_get("/api/rewards/summary")
    await update.message.reply_text(
        f"Твой баланс:\n"
        f"Заработано всего: ${summary['total_earned']:.2f}\n"
        f"Выплачено: ${summary['total_paid']:.2f}\n"
        f"Доступно: ${summary['balance']:.2f}\n"
        f"Серия: {summary['streak_days']} дней подряд"
    )

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "show_all":
        msg, kb = await build_today_message()
        await q.edit_message_text(msg, reply_markup=kb)
        return

    if data.startswith("done:"):
        ex_id = int(data.split(":")[1])
        result = await api_post("/api/completions", {
            "exercise_id": ex_id, "input_type": "done"
        })
        reward = result.get("reward_earned", 0)
        await q.edit_message_text(
            f"Отлично! Упражнение выполнено!\nНачислено: +${reward:.2f}\n\nТипо так держать!"
        )
        await asyncio.sleep(1)
        msg, kb = await build_today_message()
        await ctx.bot.send_message(chat_id=q.message.chat_id, text=msg, reply_markup=kb)

    elif data.startswith("input:"):
        parts = data.split(":")
        ex_id  = int(parts[1])
        target = int(parts[2]) if len(parts) > 2 else 0
        pending_input[q.message.chat_id] = {"ex_id": ex_id, "target": target}
        await q.edit_message_text(
            f"Введи сколько повторений сделал (цель: {target}):"
        )

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in pending_input:
        await update.message.reply_text("Отправь /today чтобы увидеть задания")
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Введи число, например: 28")
        return
    value = int(text)
    info  = pending_input.pop(chat_id)
    result = await api_post("/api/completions", {
        "exercise_id": info["ex_id"],
        "value_done":  value,
        "value_target": info["target"],
        "input_type":  "reps"
    })
    reward = result.get("reward_earned", 0)
    pct = round(value / info["target"] * 100) if info["target"] else 100
    await update.message.reply_text(
        f"Записал: {value} повторений ({pct}%)\nНачислено: +${reward:.2f}"
    )
    msg, kb = await build_today_message()
    await update.message.reply_text(msg, reply_markup=kb)

# ---- Main ----
async def main():
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN not set. Bot won't start.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("today",   cmd_today))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    scheduler = AsyncIOScheduler()
    scheduler.start()
    await reload_schedules(scheduler, app)

    log.info("Swim Trainer Bot started")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
