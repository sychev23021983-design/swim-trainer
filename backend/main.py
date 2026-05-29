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
