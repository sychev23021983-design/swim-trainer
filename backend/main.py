import os, sqlite3, jwt, json, asyncio, hashlib
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import aiofiles
import httpx

DB_PATH    = os.getenv("DB_PATH", "./data/swim.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
PARENT_PWD = os.getenv("PARENT_PASSWORD", "parent123")
CHILD_NAME = os.getenv("CHILD_NAME", "Сын")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ---------- DB ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS exercises (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        category    TEXT NOT NULL,
        sub_category TEXT DEFAULT 'general',
        difficulty  INTEGER DEFAULT 1,
        sets        INTEGER DEFAULT 3,
        reps        INTEGER,
        duration_sec INTEGER,
        rest_sec    INTEGER DEFAULT 45,
        reward_usd  REAL DEFAULT 0.10,
        input_type  TEXT DEFAULT 'done',
        muscles_primary   TEXT DEFAULT '[]',
        muscles_secondary TEXT DEFAULT '[]',
        muscles_stabilizer TEXT DEFAULT '[]',
        swim_benefit TEXT DEFAULT '',
        instructions TEXT DEFAULT '',
        tips        TEXT DEFAULT '',
        image_muscle TEXT DEFAULT '',
        image_demo  TEXT DEFAULT '',
        active      INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS schedules (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
        frequency   TEXT DEFAULT '3x_week',
        days        TEXT DEFAULT '["mon","wed","fri"]',
        notify_time TEXT DEFAULT '17:00',
        active      INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS completions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER REFERENCES exercises(id),
        completed_at TEXT DEFAULT (datetime('now')),
        value_done  INTEGER,
        value_target INTEGER,
        input_type  TEXT,
        reward_earned REAL DEFAULT 0,
        note        TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS swim_results (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        style       TEXT NOT NULL,
        distance_m  INTEGER NOT NULL,
        time_sec    REAL NOT NULL,
        recorded_at TEXT DEFAULT (datetime('now')),
        note        TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS rewards (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        amount_usd  REAL NOT NULL,
        reason      TEXT DEFAULT '',
        earned_at   TEXT DEFAULT (datetime('now')),
        paid        INTEGER DEFAULT 0
    );
    """)
    db.commit()
    db.close()

# ---------- Auth ----------
security = HTTPBearer(auto_error=False)

def create_token(role: str):
    return jwt.encode({"role": role, "exp": datetime.utcnow() + timedelta(days=30)}, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(401, "Invalid token")

# ---------- Models ----------
class LoginReq(BaseModel):
    password: str

class ExerciseCreate(BaseModel):
    title: str
    category: str
    sub_category: str = "general"
    difficulty: int = 1
    sets: int = 3
    reps: Optional[int] = None
    duration_sec: Optional[int] = None
    rest_sec: int = 45
    reward_usd: float = 0.10
    input_type: str = "done"
    muscles_primary: List[str] = []
    muscles_secondary: List[str] = []
    muscles_stabilizer: List[str] = []
    swim_benefit: str = ""
    instructions: str = ""
    tips: str = ""
    active: bool = True

class ScheduleCreate(BaseModel):
    exercise_id: int
    frequency: str = "3x_week"
    days: List[str] = ["mon","wed","fri"]
    notify_time: str = "17:00"
    active: bool = True

class CompletionCreate(BaseModel):
    exercise_id: int
    value_done: Optional[int] = None
    value_target: Optional[int] = None
    input_type: str = "done"
    note: str = ""

class SwimResultCreate(BaseModel):
    style: str
    distance_m: int
    time_sec: float
    note: str = ""

# ---------- App ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Swim Trainer API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------- Routes: Auth ----------
@app.get("/api/health")
def health(): return {"status": "ok"}

@app.post("/api/auth/login")
def login(req: LoginReq):
    if req.password == PARENT_PWD:
        return {"token": create_token("parent"), "role": "parent", "child_name": CHILD_NAME}
    raise HTTPException(401, "Wrong password")

@app.get("/api/auth/me")
def me(user=Depends(verify_token)):
    return {"role": user["role"], "child_name": CHILD_NAME}

# ---------- Routes: Exercises ----------
@app.get("/api/exercises")
def list_exercises(category: str = None, active: int = None):
    db = get_db()
    q = "SELECT * FROM exercises WHERE 1=1"
    params = []
    if category: q += " AND category=?"; params.append(category)
    if active is not None: q += " AND active=?"; params.append(active)
    q += " ORDER BY category, difficulty, id"
    rows = db.execute(q, params).fetchall()
    db.close()
    result = []
    for r in rows:
        d = dict(r)
        d["muscles_primary"]   = json.loads(d["muscles_primary"])
        d["muscles_secondary"] = json.loads(d["muscles_secondary"])
        d["muscles_stabilizer"]= json.loads(d["muscles_stabilizer"])
        result.append(d)
    return result

@app.get("/api/exercises/{ex_id}")
def get_exercise(ex_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM exercises WHERE id=?", (ex_id,)).fetchone()
    db.close()
    if not row: raise HTTPException(404, "Not found")
    d = dict(row)
    d["muscles_primary"]   = json.loads(d["muscles_primary"])
    d["muscles_secondary"] = json.loads(d["muscles_secondary"])
    d["muscles_stabilizer"]= json.loads(d["muscles_stabilizer"])
    return d

@app.post("/api/exercises")
def create_exercise(ex: ExerciseCreate, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    cur = db.execute("""
        INSERT INTO exercises (title,category,sub_category,difficulty,sets,reps,duration_sec,
            rest_sec,reward_usd,input_type,muscles_primary,muscles_secondary,muscles_stabilizer,
            swim_benefit,instructions,tips,active)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (ex.title, ex.category, ex.sub_category, ex.difficulty,
          ex.sets, ex.reps, ex.duration_sec, ex.rest_sec, ex.reward_usd, ex.input_type,
          json.dumps(ex.muscles_primary, ensure_ascii=False),
          json.dumps(ex.muscles_secondary, ensure_ascii=False),
          json.dumps(ex.muscles_stabilizer, ensure_ascii=False),
          ex.swim_benefit, ex.instructions, ex.tips, int(ex.active)))
    db.commit()
    new_id = cur.lastrowid
    db.close()
    return {"id": new_id}

@app.put("/api/exercises/{ex_id}")
def update_exercise(ex_id: int, ex: ExerciseCreate, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    db.execute("""
        UPDATE exercises SET title=?,category=?,sub_category=?,difficulty=?,sets=?,reps=?,
            duration_sec=?,rest_sec=?,reward_usd=?,input_type=?,muscles_primary=?,
            muscles_secondary=?,muscles_stabilizer=?,swim_benefit=?,instructions=?,tips=?,active=?
        WHERE id=?
    """, (ex.title, ex.category, ex.sub_category, ex.difficulty,
          ex.sets, ex.reps, ex.duration_sec, ex.rest_sec, ex.reward_usd, ex.input_type,
          json.dumps(ex.muscles_primary, ensure_ascii=False),
          json.dumps(ex.muscles_secondary, ensure_ascii=False),
          json.dumps(ex.muscles_stabilizer, ensure_ascii=False),
          ex.swim_benefit, ex.instructions, ex.tips, int(ex.active), ex_id))
    db.commit()
    db.close()
    return {"ok": True}

@app.delete("/api/exercises/{ex_id}")
def delete_exercise(ex_id: int, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    db.execute("DELETE FROM exercises WHERE id=?", (ex_id,))
    db.commit()
    db.close()
    return {"ok": True}

# ---------- Routes: Schedules ----------
@app.get("/api/schedules")
def list_schedules(user=Depends(verify_token)):
    db = get_db()
    rows = db.execute("""
        SELECT s.*, e.title, e.category, e.reward_usd
        FROM schedules s JOIN exercises e ON s.exercise_id=e.id
        ORDER BY s.notify_time
    """).fetchall()
    db.close()
    result = []
    for r in rows:
        d = dict(r)
        d["days"] = json.loads(d["days"])
        result.append(d)
    return result

@app.post("/api/schedules")
def create_schedule(s: ScheduleCreate, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    cur = db.execute(
        "INSERT INTO schedules (exercise_id,frequency,days,notify_time,active) VALUES (?,?,?,?,?)",
        (s.exercise_id, s.frequency, json.dumps(s.days), s.notify_time, int(s.active))
    )
    db.commit()
    new_id = cur.lastrowid
    db.close()
    return {"id": new_id}

@app.delete("/api/schedules/{sid}")
def delete_schedule(sid: int, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    db.execute("DELETE FROM schedules WHERE id=?", (sid,))
    db.commit(); db.close()
    return {"ok": True}

# ---------- Routes: Today's tasks ----------
DAY_MAP = {"Monday":"mon","Tuesday":"tue","Wednesday":"wed","Thursday":"thu",
           "Friday":"fri","Saturday":"sat","Sunday":"sun"}

@app.get("/api/today")
def get_today_tasks():
    today_name = datetime.now().strftime("%A")
    today_code = DAY_MAP.get(today_name, "mon")
    today_str  = datetime.now().strftime("%Y-%m-%d")
    db = get_db()
    schedules = db.execute("""
        SELECT s.*, e.title, e.category, e.reward_usd, e.sets, e.reps,
               e.duration_sec, e.rest_sec, e.input_type, e.difficulty,
               e.swim_benefit, e.instructions, e.tips,
               e.muscles_primary, e.muscles_secondary, e.muscles_stabilizer
        FROM schedules s JOIN exercises e ON s.exercise_id=e.id
        WHERE s.active=1 AND e.active=1
    """).fetchall()
    tasks = []
    for s in schedules:
        d = dict(s)
        days = json.loads(d["days"])
        if today_code not in days: continue
        done_today = db.execute(
            "SELECT id FROM completions WHERE exercise_id=? AND date(completed_at)=?",
            (d["exercise_id"], today_str)
        ).fetchone()
        d["completed_today"] = done_today is not None
        d["muscles_primary"]   = json.loads(d["muscles_primary"])
        d["muscles_secondary"] = json.loads(d["muscles_secondary"])
        d["muscles_stabilizer"]= json.loads(d["muscles_stabilizer"])
        tasks.append(d)
    db.close()
    return tasks

# ---------- Routes: Completions ----------
@app.post("/api/completions")
def add_completion(c: CompletionCreate):
    db = get_db()
    ex = db.execute("SELECT reward_usd FROM exercises WHERE id=?", (c.exercise_id,)).fetchone()
    if not ex: raise HTTPException(404)
    reward = ex["reward_usd"]
    db.execute("""
        INSERT INTO completions (exercise_id,value_done,value_target,input_type,reward_earned,note)
        VALUES (?,?,?,?,?,?)
    """, (c.exercise_id, c.value_done, c.value_target, c.input_type, reward, c.note))
    db.execute("INSERT INTO rewards (amount_usd,reason) VALUES (?,?)",
               (reward, f"Выполнено упражнение #{c.exercise_id}"))
    db.commit()
    db.close()
    return {"ok": True, "reward_earned": reward}

# Internal endpoint for bot (no JWT, uses BOT_SECRET)
BOT_SECRET = os.getenv("BOT_SECRET", "swim-bot-internal-2026")

class BotCompletionCreate(BaseModel):
    exercise_id: int
    value_done: Optional[int] = None
    value_target: Optional[int] = None
    input_type: str = "done"
    bot_secret: str = ""

@app.post("/api/bot/complete")
def bot_complete(c: BotCompletionCreate):
    """Called by Telegram bot — no JWT needed, uses shared secret."""
    if c.bot_secret != BOT_SECRET:
        raise HTTPException(403, "Invalid bot secret")
    db = get_db()
    ex = db.execute("SELECT reward_usd FROM exercises WHERE id=?", (c.exercise_id,)).fetchone()
    if not ex: raise HTTPException(404)
    reward = ex["reward_usd"]
    db.execute("""
        INSERT INTO completions (exercise_id,value_done,value_target,input_type,reward_earned)
        VALUES (?,?,?,?,?)
    """, (c.exercise_id, c.value_done, c.value_target, c.input_type, reward))
    db.execute("INSERT INTO rewards (amount_usd,reason) VALUES (?,?)",
               (reward, f"Выполнено упражнение #{c.exercise_id} (Telegram)"))
    db.commit()
    db.close()
    return {"ok": True, "reward_earned": reward}

@app.get("/api/bot/today")
def bot_today(bot_secret: str = ""):
    """Today tasks for bot — no JWT."""
    if bot_secret != BOT_SECRET:
        raise HTTPException(403, "Invalid bot secret")
    return get_today_tasks()

@app.get("/api/completions")
def list_completions(days: int = 30, user=Depends(verify_token)):
    db = get_db()
    rows = db.execute("""
        SELECT c.*, e.title, e.category
        FROM completions c JOIN exercises e ON c.exercise_id=e.id
        WHERE c.completed_at >= datetime('now', ?)
        ORDER BY c.completed_at DESC
    """, (f"-{days} days",)).fetchall()
    db.close()
    return [dict(r) for r in rows]

# ---------- Routes: Swim Results ----------
@app.get("/api/swim-results")
def list_swim_results(style: str = None, user=Depends(verify_token)):
    db = get_db()
    q = "SELECT * FROM swim_results WHERE 1=1"
    params = []
    if style: q += " AND style=?"; params.append(style)
    q += " ORDER BY recorded_at DESC"
    rows = db.execute(q, params).fetchall()
    db.close()
    return [dict(r) for r in rows]

@app.post("/api/swim-results")
def add_swim_result(r: SwimResultCreate, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    cur = db.execute(
        "INSERT INTO swim_results (style,distance_m,time_sec,note) VALUES (?,?,?,?)",
        (r.style, r.distance_m, r.time_sec, r.note)
    )
    db.commit()
    db.close()
    return {"id": cur.lastrowid}

@app.delete("/api/swim-results/{rid}")
def delete_swim_result(rid: int, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    db.execute("DELETE FROM swim_results WHERE id=?", (rid,))
    db.commit(); db.close()
    return {"ok": True}

# ---------- Routes: Rewards ----------
@app.get("/api/rewards/summary")
def rewards_summary():
    db = get_db()
    total  = db.execute("SELECT COALESCE(SUM(amount_usd),0) as t FROM rewards").fetchone()["t"]
    paid   = db.execute("SELECT COALESCE(SUM(amount_usd),0) as t FROM rewards WHERE paid=1").fetchone()["t"]
    streak = _calc_streak(db)
    db.close()
    return {"total_earned": round(total, 2), "total_paid": round(paid, 2),
            "balance": round(total - paid, 2), "streak_days": streak}

@app.get("/api/rewards")
def list_rewards(user=Depends(verify_token)):
    db = get_db()
    rows = db.execute("SELECT * FROM rewards ORDER BY earned_at DESC LIMIT 50").fetchall()
    db.close()
    return [dict(r) for r in rows]

@app.post("/api/rewards/{rid}/pay")
def mark_paid(rid: int, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    db.execute("UPDATE rewards SET paid=1 WHERE id=?", (rid,))
    db.commit(); db.close()
    return {"ok": True}

def _calc_streak(db):
    rows = db.execute(
        "SELECT DISTINCT date(completed_at) as d FROM completions ORDER BY d DESC"
    ).fetchall()
    if not rows: return 0
    streak = 0
    today = datetime.now().date()
    for i, r in enumerate(rows):
        d = datetime.strptime(r["d"], "%Y-%m-%d").date()
        if (today - d).days == i: streak += 1
        else: break
    return streak

# ---------- Routes: Progress / Stats ----------
@app.get("/api/stats/progress")
def progress_stats(user=Depends(verify_token)):
    db = get_db()
    weekly = db.execute("""
        SELECT date(completed_at) as day, COUNT(*) as count, SUM(reward_earned) as earned
        FROM completions WHERE completed_at >= datetime('now','-28 days')
        GROUP BY day ORDER BY day
    """).fetchall()
    by_cat = db.execute("""
        SELECT e.category, COUNT(*) as count
        FROM completions c JOIN exercises e ON c.exercise_id=e.id
        WHERE c.completed_at >= datetime('now','-30 days')
        GROUP BY e.category
    """).fetchall()
    db.close()
    return {
        "weekly": [dict(r) for r in weekly],
        "by_category": [dict(r) for r in by_cat]
    }

@app.get("/api/stats/swim-progress")
def swim_progress(user=Depends(verify_token)):
    db = get_db()
    rows = db.execute("""
        SELECT style, distance_m, time_sec, recorded_at
        FROM swim_results ORDER BY style, recorded_at
    """).fetchall()
    db.close()
    by_style = {}
    for r in rows:
        d = dict(r)
        s = d["style"]
        if s not in by_style: by_style[s] = []
        pace = round(d["time_sec"] / (d["distance_m"]/100), 2)
        d["pace_per_100m"] = pace
        by_style[s].append(d)
    return by_style

# ---------- Upload image ----------
@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg","jpeg","png","gif","svg","webp"]:
        raise HTTPException(400, "Unsupported file type")
    fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    async with aiofiles.open(fpath, "wb") as f:
        await f.write(await file.read())
    return {"url": f"/uploads/{fname}"}

# ---------- Settings ----------
ENV_PATH = "/app/data/.env.runtime"
SETTINGS_KEYS = ["child_name", "parent_password", "telegram_bot_token", "telegram_chat_id"]

# In-memory cache for token (survives between requests in same process)
_token_cache: dict = {}

def _read_settings() -> dict:
    result = {
        "child_name":         os.getenv("CHILD_NAME", ""),
        "parent_password":    "",
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id":   os.getenv("TELEGRAM_CHAT_ID", ""),
    }
    # Override with runtime file if exists
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k2 = k.strip().lower()
                    if k2 in SETTINGS_KEYS:
                        result[k2] = v.strip()
    # Override with in-memory cache (most recent save)
    for k, v in _token_cache.items():
        if v:
            result[k] = v
    return result

def _write_settings(data: dict):
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w") as f:
        for k in SETTINGS_KEYS:
            v = data.get(k, "")
            f.write(f"{k.upper()}={v}\n")
    # Update in-memory cache immediately
    for k in SETTINGS_KEYS:
        if data.get(k):
            _token_cache[k] = data[k]

class SettingsModel(BaseModel):
    child_name: str = ""
    parent_password: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

@app.get("/api/settings")
def get_settings(user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    s = _read_settings()
    # Mask token for display but keep chat_id visible
    s["telegram_bot_token"] = "***SAVED***" if s.get("telegram_bot_token") else ""
    return s

@app.post("/api/settings")
def save_settings(s: SettingsModel, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    current = _read_settings()
    data = s.dict()
    # Don't overwrite token if user didn't change it (masked value)
    if data["telegram_bot_token"] in ("***SAVED***", "***", ""):
        if not data["telegram_bot_token"]:
            data["telegram_bot_token"] = ""
        else:
            data["telegram_bot_token"] = current.get("telegram_bot_token", "")
    # Apply in-memory immediately (no restart needed)
    if data.get("parent_password"):
        global PARENT_PWD
        PARENT_PWD = data["parent_password"]
    if data.get("child_name"):
        global CHILD_NAME
        CHILD_NAME = data["child_name"]
    _write_settings(data)
    return {"ok": True, "message": "Настройки сохранены"}

@app.post("/api/settings/test-telegram")
async def test_telegram(user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    s = _read_settings()
    token   = s.get("telegram_bot_token", "").strip()
    chat_id = s.get("telegram_chat_id", "").strip()
    if not token:
        raise HTTPException(400, detail="Bot Token не заполнен. Сохрани настройки сначала.")
    if not chat_id:
        raise HTTPException(400, detail="Chat ID не заполнен.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(url, json={
                "chat_id": chat_id,
                "text": "🏊 Swim Trainer подключён!\nБот работает. Можно тренироваться 💪",
                "parse_mode": "HTML"
            })
        if r.status_code == 200:
            return {"ok": True, "message": "Сообщение отправлено!"}
        else:
            err = r.json()
            description = err.get("description", r.text)
            raise HTTPException(400, detail=f"Telegram: {description}")
    except httpx.TimeoutException:
        raise HTTPException(400, detail="Telegram не отвечает (timeout). Проверь токен.")
    except httpx.RequestError as e:
        raise HTTPException(400, detail=f"Сетевая ошибка: {str(e)}")

# ---------- Send single exercise to Telegram ----------
CAT_EMOJI = {
    "butterfly": "🦋", "freestyle": "🏊", "backstroke": "🔄",
    "breaststroke": "🐸", "universal": "🏋️"
}
CAT_LABELS = {
    "butterfly": "Баттерфляй", "freestyle": "Кроль",
    "backstroke": "На спине", "breaststroke": "Брасс", "universal": "Универсальное"
}

@app.post("/api/exercises/{ex_id}/send-telegram")
async def send_exercise_telegram(ex_id: int, user=Depends(verify_token)):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    ex = db.execute("SELECT * FROM exercises WHERE id=?", (ex_id,)).fetchone()
    db.close()
    if not ex: raise HTTPException(404, "Упражнение не найдено")

    s = _read_settings()
    token   = s.get("telegram_bot_token", "").strip()
    chat_id = s.get("telegram_chat_id", "").strip()
    if not token or not chat_id:
        raise HTTPException(400, detail="Telegram не настроен. Заполни Bot Token и Chat ID в Настройках.")

    ex = dict(ex)
    emoji    = CAT_EMOJI.get(ex["category"], "💪")
    cat_label= CAT_LABELS.get(ex["category"], ex["category"].upper())
    reps_str = (f"{ex['sets']} × {ex['reps']} повт." if ex.get("reps")
                else f"{ex['sets']} подх. × {ex['duration_sec']} сек" if ex.get("duration_sec")
                else f"{ex['sets']} подходов")
    diff_str = "★" * ex["difficulty"] + "☆" * (3 - ex["difficulty"])

    text = (
        f"{emoji} <b>{cat_label} — Задание от папы!</b>\n\n"
        f"<b>{ex['title']}</b>\n"
        f"{diff_str}  |  {reps_str}  |  отдых {ex['rest_sec']} сек"
    )
    if ex.get("instructions"):
        text += f"\n\n📋 {ex['instructions']}"
    if ex.get("tips"):
        text += f"\n💡 <i>{ex['tips']}</i>"
    if ex.get("swim_benefit"):
        text += f"\n\n🏊 {ex['swim_benefit']}"
    text += f"\n\n💰 <b>Награда: ${ex['reward_usd']:.2f}</b>"

    # Inline keyboard
    input_type = ex.get("input_type", "done")
    reps_target = ex.get("reps") or 0
    if input_type == "done":
        kb_buttons = [[{"text": "✅ Выполнил!", "callback_data": f"done:{ex_id}"}]]
    else:
        kb_buttons = [[
            {"text": "✅ Выполнил всё!", "callback_data": f"done:{ex_id}"},
            {"text": "🔢 Ввести кол-во", "callback_data": f"input:{ex_id}:{reps_target}"}
        ]]
    kb_buttons.append([{"text": "📋 Все задания дня", "callback_data": "show_all"}])
    reply_markup = {"inline_keyboard": kb_buttons}

    tg_base = f"https://api.telegram.org/bot{token}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            # Try to send with photo if image_demo exists
            image_path = ex.get("image_demo") or ex.get("image_muscle")
            sent = False
            if image_path:
                full_path = os.path.join(UPLOAD_DIR, os.path.basename(image_path))
                if os.path.exists(full_path):
                    caption = text[:1024]  # Telegram caption limit
                    with open(full_path, "rb") as img_file:
                        files = {"photo": img_file}
                        data  = {"chat_id": chat_id, "caption": caption,
                                 "parse_mode": "HTML",
                                 "reply_markup": json.dumps(reply_markup)}
                        r = await c.post(f"{tg_base}/sendPhoto", data=data, files=files)
                    if r.status_code == 200:
                        sent = True

            if not sent:
                r = await c.post(f"{tg_base}/sendMessage", json={
                    "chat_id": chat_id, "text": text,
                    "parse_mode": "HTML", "reply_markup": reply_markup
                })
                if r.status_code != 200:
                    err = r.json()
                    raise HTTPException(400, detail=f"Telegram: {err.get('description', r.text)}")

        return {"ok": True, "message": f"«{ex['title']}» отправлено в Telegram!"}
    except httpx.TimeoutException:
        raise HTTPException(400, detail="Telegram не отвечает (timeout)")
    except httpx.RequestError as e:
        raise HTTPException(400, detail=f"Сетевая ошибка: {str(e)}")

@app.post("/api/exercises/{ex_id}/upload-image")
async def upload_exercise_image(
    ex_id: int,
    image_type: str = "demo",   # "demo" or "muscle"
    file: UploadFile = File(...),
    user=Depends(verify_token)
):
    if user["role"] != "parent": raise HTTPException(403)
    db = get_db()
    ex = db.execute("SELECT id FROM exercises WHERE id=?", (ex_id,)).fetchone()
    if not ex: raise HTTPException(404, "Упражнение не найдено")

    ext = (file.filename or "img").split(".")[-1].lower()
    if ext not in ["jpg","jpeg","png","gif","svg","webp"]:
        raise HTTPException(400, "Поддерживаются: jpg, png, gif, webp, svg")

    fname = f"ex_{ex_id}_{image_type}.{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    async with aiofiles.open(fpath, "wb") as f:
        await f.write(await file.read())

    url_path = f"/uploads/{fname}"
    field    = "image_demo" if image_type == "demo" else "image_muscle"
    db.execute(f"UPDATE exercises SET {field}=? WHERE id=?", (url_path, ex_id))
    db.commit()
    db.close()
    return {"ok": True, "url": url_path}
