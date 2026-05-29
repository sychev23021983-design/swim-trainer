import os, asyncio, logging, json
from datetime import datetime
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, filters, ContextTypes)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

DAY_EN = {"Monday":"mon","Tuesday":"tue","Wednesday":"wed","Thursday":"thu",
          "Friday":"fri","Saturday":"sat","Sunday":"sun"}

CAT_EMOJI  = {"butterfly":"🦋","freestyle":"🏊","backstroke":"🔄","breaststroke":"🐸","universal":"🏋️"}
CAT_LABELS = {"butterfly":"БАТТЕРФЛЯЙ","freestyle":"КРОЛЬ","backstroke":"НА СПИНЕ",
              "breaststroke":"БРАСС","universal":"ОБЩЕЕ"}
DIFF_STARS = {1:"★☆☆", 2:"★★☆", 3:"★★★"}

pending_input: dict = {}  # chat_id -> {ex_id, target}

# ── API helpers ────────────────────────────────────────────────────────────────
async def api_get(path: str):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()

async def api_post(path: str, data: dict = None):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BACKEND_URL}{path}", json=data or {})
        r.raise_for_status()
        return r.json()

# ── Format single exercise message ────────────────────────────────────────────
def format_exercise_msg(ex: dict, idx: int = 1, total: int = 1, show_reward: bool = True) -> str:
    cat   = ex.get("category", "universal")
    emoji = CAT_EMOJI.get(cat, "💪")
    label = CAT_LABELS.get(cat, cat.upper())
    diff  = DIFF_STARS.get(ex.get("difficulty", 1), "★☆☆")

    reps_str = (f"{ex['sets']} × {ex['reps']} повт."
                if ex.get("reps") else
                f"{ex['sets']} подх. × {ex['duration_sec']} сек"
                if ex.get("duration_sec") else
                f"{ex['sets']} подходов")

    lines = [
        f"{emoji} <b>{label}</b>",
        f"",
        f"<b>{ex['title']}</b>",
        f"{diff}  |  {reps_str}  |  отдых {ex.get('rest_sec', 45)} сек",
    ]
    if ex.get("instructions"):
        lines += ["", f"📋 {ex['instructions']}"]
    if ex.get("tips"):
        lines += [f"💡 <i>{ex['tips']}</i>"]
    if ex.get("swim_benefit"):
        lines += ["", f"🏊 {ex['swim_benefit']}"]
    if show_reward:
        lines += ["", f"💰 <b>Награда: ${ex.get('reward_usd', 0):.2f}</b>"]
    if total > 1:
        lines += ["", f"<i>Задание {idx} из {total}</i>"]
    return "\n".join(lines)

def exercise_keyboard(ex_id: int, input_type: str, target: int = 0) -> InlineKeyboardMarkup:
    """Inline keyboard for a single exercise."""
    if input_type == "done":
        buttons = [[InlineKeyboardButton("✅ Выполнил!", callback_data=f"done:{ex_id}")]]
    else:
        buttons = [
            [InlineKeyboardButton("✅ Выполнил всё!", callback_data=f"done:{ex_id}"),
             InlineKeyboardButton(f"🔢 Ввести кол-во", callback_data=f"input:{ex_id}:{target}")],
        ]
    buttons.append([InlineKeyboardButton("📋 Все задания дня", callback_data="show_all")])
    return InlineKeyboardMarkup(buttons)

# ── Today summary ──────────────────────────────────────────────────────────────
async def build_today_summary() -> tuple[str, InlineKeyboardMarkup | None]:
    tasks   = await api_get("/api/today")
    summary = await api_get("/api/rewards/summary")
    today   = datetime.now().strftime("%d.%m.%Y")

    if not tasks:
        return f"На сегодня ({today}) тренировок нет. Отдыхай! 🎉", None

    pending = [t for t in tasks if not t.get("completed_today")]
    done    = [t for t in tasks if t.get("completed_today")]

    lines = [f"⏰ <b>Время стать на 1% лучше!</b>  {today}", ""]

    if pending:
        lines.append(f"📌 <b>Сегодня ({len(pending)} заданий):</b>")
        total_reward = sum(t.get("reward_usd", 0) for t in pending)
        for t in pending:
            emoji = CAT_EMOJI.get(t.get("category",""), "•")
            reps  = f"{t['sets']}×{t['reps']}" if t.get("reps") else f"{t.get('duration_sec','')}сек"
            lines.append(f"  {emoji} {t['title']} — {reps} (+${t.get('reward_usd',0):.2f})")
        lines += ["", f"💰 Всего за выполнение: <b>${total_reward:.2f}</b>"]

    if done:
        lines += ["", f"✅ <b>Выполнено ({len(done)}):</b>"]
        for t in done:
            lines.append(f"  ✓ {t['title']}")

    lines += ["", f"🏦 Баланс: <b>${summary.get('balance', 0):.2f}</b>"]
    if summary.get("streak_days", 0) > 1:
        lines.append(f"🔥 Серия: {summary['streak_days']} дней подряд!")

    if not pending:
        return "\n".join(lines), None

    # Buttons: one per pending task + full list
    buttons = []
    for t in pending:
        emoji = CAT_EMOJI.get(t.get("category",""), "💪")
        label = f"{emoji} {t['title'][:28]}"
        buttons.append([InlineKeyboardButton(label,
            callback_data=f"show_ex:{t['exercise_id']}")])

    return "\n".join(lines), InlineKeyboardMarkup(buttons)

# ── Send single exercise (with photo if available) ────────────────────────────
async def send_single_exercise(bot, chat_id: str, ex: dict,
                                idx: int = 1, total: int = 1):
    text = format_exercise_msg(ex, idx, total)
    kb   = exercise_keyboard(ex["exercise_id"] if "exercise_id" in ex else ex["id"],
                             ex.get("input_type","done"),
                             ex.get("reps", 0) or 0)
    image_url = ex.get("image_demo") or ex.get("image_muscle")
    if image_url and image_url.startswith("/uploads/"):
        photo_url = f"{BACKEND_URL}{image_url}"
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                resp = await c.get(photo_url)
            if resp.status_code == 200:
                await bot.send_photo(chat_id=chat_id, photo=resp.content,
                                     caption=text, parse_mode="HTML", reply_markup=kb)
                return
        except Exception as e:
            log.warning(f"Photo send failed: {e}")
    # Fallback: text only
    await bot.send_message(chat_id=chat_id, text=text,
                           parse_mode="HTML", reply_markup=kb)

# ── Scheduler ─────────────────────────────────────────────────────────────────
async def send_daily(app: Application):
    if not CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID not set"); return
    try:
        tasks = await api_get("/api/today")
        if not tasks: return
        pending = [t for t in tasks if not t.get("completed_today")]
        if not pending: return

        # Send summary first
        msg, kb = await build_today_summary()
        await app.bot.send_message(chat_id=CHAT_ID, text=msg,
                                   parse_mode="HTML", reply_markup=kb)

        log.info(f"Sent daily summary: {len(pending)} tasks")
    except Exception as e:
        log.error(f"send_daily error: {e}")

async def reload_schedules(scheduler: AsyncIOScheduler, app: Application):
    for job in scheduler.get_jobs():
        if job.id.startswith("notify_"):
            job.remove()
    try:
        schedules = await api_get("/api/schedules")
        times_seen = set()
        for s in schedules:
            if not s.get("active"): continue
            t = s.get("notify_time", "17:00")
            if t in times_seen: continue
            times_seen.add(t)
            h, m = map(int, t.split(":"))
            scheduler.add_job(send_daily, "cron", hour=h, minute=m,
                              id=f"notify_{t.replace(':','')}", args=[app])
            log.info(f"Scheduled notification at {t}")
    except Exception as e:
        log.error(f"reload_schedules error: {e}")

# ── Handlers ──────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, kb = await build_today_summary()
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, kb = await build_today_summary()
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = await api_get("/api/rewards/summary")
    await update.message.reply_text(
        f"💰 <b>Твои награды</b>\n\n"
        f"Заработано: <b>${s['total_earned']:.2f}</b>\n"
        f"Выплачено:  ${s['total_paid']:.2f}\n"
        f"<b>Доступно:   ${s['balance']:.2f}</b>\n\n"
        f"🔥 Серия: {s['streak_days']} дней подряд",
        parse_mode="HTML"
    )

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    data = q.data

    # ── Show today summary ──
    if data == "show_all":
        msg, kb = await build_today_summary()
        await ctx.bot.send_message(chat_id=q.message.chat_id, text=msg,
                                   parse_mode="HTML", reply_markup=kb)
        return

    # ── Show single exercise ──
    if data.startswith("show_ex:"):
        ex_id = int(data.split(":")[1])
        try:
            tasks = await api_get("/api/today")
            ex = next((t for t in tasks if t.get("exercise_id") == ex_id), None)
            if not ex:
                ex_data = await api_get(f"/api/exercises/{ex_id}")
                ex_data["exercise_id"] = ex_id
                ex = ex_data
            await send_single_exercise(ctx.bot, q.message.chat_id, ex)
        except Exception as e:
            await ctx.bot.send_message(chat_id=q.message.chat_id,
                                       text=f"Не удалось загрузить упражнение: {e}")
        return

    # ── Mark done ──
    if data.startswith("done:"):
        ex_id = int(data.split(":")[1])
        result = await api_post("/api/completions", {
            "exercise_id": ex_id, "input_type": "done"
        })
        reward = result.get("reward_earned", 0)
        await q.edit_message_caption(
            caption=f"✅ <b>Выполнено!</b>\nНачислено: <b>+${reward:.2f}</b>\n\nТак держать! 💪",
            parse_mode="HTML"
        ) if q.message.caption else await q.edit_message_text(
            text=f"✅ <b>Выполнено!</b>\nНачислено: <b>+${reward:.2f}</b>\n\nТак держать! 💪",
            parse_mode="HTML"
        )
        await asyncio.sleep(1)
        msg, kb = await build_today_summary()
        await ctx.bot.send_message(chat_id=q.message.chat_id, text=msg,
                                   parse_mode="HTML", reply_markup=kb)
        return

    # ── Ask for reps input ──
    if data.startswith("input:"):
        parts  = data.split(":")
        ex_id  = int(parts[1])
        target = int(parts[2]) if len(parts) > 2 else 0
        pending_input[q.message.chat_id] = {"ex_id": ex_id, "target": target}
        edit_fn = q.edit_message_caption if q.message.caption else q.edit_message_text
        kwargs = {"parse_mode": "HTML"}
        if q.message.caption:
            kwargs["caption"] = f"🔢 Сколько повторений сделал?\n<i>(цель: {target})</i>"
        else:
            kwargs["text"] = f"🔢 Сколько повторений сделал?\n<i>(цель: {target})</i>"
        await edit_fn(**kwargs)
        return

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in pending_input:
        await update.message.reply_text(
            "Отправь /today чтобы увидеть задания дня 📋",
            parse_mode="HTML"
        )
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Введи число, например: <b>28</b>", parse_mode="HTML")
        return

    value = int(text)
    info  = pending_input.pop(chat_id)
    result = await api_post("/api/completions", {
        "exercise_id":  info["ex_id"],
        "value_done":   value,
        "value_target": info["target"],
        "input_type":   "reps"
    })
    reward = result.get("reward_earned", 0)
    pct    = round(value / info["target"] * 100) if info["target"] else 100

    await update.message.reply_text(
        f"✅ <b>Записал: {value} повторений</b> ({pct}%)\n"
        f"Начислено: <b>+${reward:.2f}</b> 💰",
        parse_mode="HTML"
    )
    msg, kb = await build_today_summary()
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN not set. Waiting..."); 
        await asyncio.sleep(3600)
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

    log.info("Swim Trainer Bot started 🏊")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
