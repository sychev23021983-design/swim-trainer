#!/usr/bin/env python3
"""
Swim Trainer — seeder упражнений
Запуск: python3 seeder.py
или через контейнер: docker exec swim-trainer-backend python3 /app/seeder.py
"""
import sqlite3, json, os, sys

DB_PATH = os.getenv("DB_PATH", "./data/swim.db")

EXERCISES = [

  # ─────────────────────────────────────────────
  # UNIVERSAL — База: стабилизация корпуса
  # Слайд 3 презентации
  # ─────────────────────────────────────────────
  {
    "title":        "Планка (Streamline plank)",
    "category":     "universal",
    "sub_category": "core",
    "difficulty":   1,
    "sets":         3,
    "reps":         None,
    "duration_sec": 30,
    "rest_sec":     30,
    "reward_usd":   0.15,
    "input_type":   "done",
    "muscles_primary":    ["поперечная мышца живота", "косые мышцы живота"],
    "muscles_secondary":  ["прямая мышца живота", "передняя зубчатая"],
    "muscles_stabilizer": ["глубокие мышцы-стабилизаторы", "разгибатели позвоночника"],
    "swim_benefit": "Жёсткий мышечный корсет предотвращает провисание таза — идеальная обтекаемость (streamline) во всех стилях",
    "instructions": "Упор лёжа на предплечьях. Тело — прямая линия от головы до пяток. Таз не поднимать и не опускать. Смотреть в пол.",
    "tips":         "Представь, что тело — стрела в воде. Напряги живот так, будто ждёшь удар. Дыши ровно.",
    "tags":         ["streamline", "базовое", "без инвентаря", "все стили"],
    "active":       True,
  },
  {
    "title":        "Боковая планка",
    "category":     "universal",
    "sub_category": "core",
    "difficulty":   2,
    "sets":         3,
    "reps":         None,
    "duration_sec": 20,
    "rest_sec":     30,
    "reward_usd":   0.15,
    "input_type":   "done",
    "muscles_primary":    ["косые мышцы живота", "поперечная мышца живота"],
    "muscles_secondary":  ["средняя ягодичная", "приводящие бедра"],
    "muscles_stabilizer": ["глубокие стабилизаторы", "квадратная мышца поясницы"],
    "swim_benefit": "Боковая стабильность корпуса — тело не виляет при вращении в кроле и на спине",
    "instructions": "Упор на одно предплечье, тело боком. Бёдра оторвать от пола, держать прямую линию. Повторить на другую сторону.",
    "tips":         "Не давай бёдрам провисать. Взгляд вперёд, не вниз.",
    "tags":         ["streamline", "без инвентаря", "кор", "ротация"],
    "active":       True,
  },
  {
    "title":        "Удержание Streamline (лёжа на спине)",
    "category":     "universal",
    "sub_category": "core",
    "difficulty":   1,
    "sets":         3,
    "reps":         None,
    "duration_sec": 20,
    "rest_sec":     20,
    "reward_usd":   0.10,
    "input_type":   "done",
    "muscles_primary":    ["поперечная мышца живота", "передняя зубчатая"],
    "muscles_secondary":  ["прямая мышца живота"],
    "muscles_stabilizer": ["глубокие мышцы-стабилизаторы"],
    "swim_benefit": "Тренирует горизонтальное положение тела — снижает лобовое гидродинамическое сопротивление (drag)",
    "instructions": "Лечь на спину, руки вытянуть над головой. Прижать поясницу к полу. Удерживать 20 сек, не прогибая спину.",
    "tips":         "Поясница должна касаться пола всё время. Если отрывается — согни колени чуть-чуть.",
    "tags":         ["streamline", "без инвентаря", "базовое", "все стили"],
    "active":       True,
  },
  {
    "title":        "Скручивания с поворотом (Russian twist)",
    "category":     "universal",
    "sub_category": "core",
    "difficulty":   2,
    "sets":         3,
    "reps":         15,
    "duration_sec": None,
    "rest_sec":     40,
    "reward_usd":   0.20,
    "input_type":   "reps",
    "muscles_primary":    ["косые мышцы живота"],
    "muscles_secondary":  ["прямая мышца живота", "сгибатели бедра"],
    "muscles_stabilizer": ["глубокие стабилизаторы"],
    "swim_benefit": "Ротационная сила кора — основа поворота корпуса в кроле и на спине для мощного гребка",
    "instructions": "Сесть, ноги приподнять. Руки сцеплены или с мячом. Поворачивать корпус влево-вправо, касаясь пола.",
    "tips":         "Движение идёт от корпуса, не от рук. Держи спину прямой.",
    "tags":         ["ротация", "кор", "без инвентаря или мяч"],
    "active":       True,
  },

  # ─────────────────────────────────────────────
  # FREESTYLE — Кроль: двигатель гребка
  # Слайды 4–5 презентации
  # ─────────────────────────────────────────────
  {
    "title":        "Гребки с эспандером (freestyle pull)",
    "category":     "freestyle",
    "sub_category": "pull",
    "difficulty":   2,
    "sets":         3,
    "reps":         12,
    "duration_sec": None,
    "rest_sec":     45,
    "reward_usd":   0.25,
    "input_type":   "reps",
    "muscles_primary":    ["широчайшие мышцы спины", "трицепс"],
    "muscles_secondary":  ["большая грудная", "дельтовидная (передняя)"],
    "muscles_stabilizer": ["ромбовидные", "трапеция (нижняя)"],
    "swim_benefit": "Широчайшие — сила захвата воды («высокий локоть»). Трицепс — взрывное ускорение в финальной фазе (push). Мощный захват и ровный баланс",
    "instructions": "Встать лицом к точке крепления эспандера. Наклон вперёд ~45°. Тянуть эспандер вдоль тела, имитируя гребок кролем: захват → тяга → толчок (push). Локоть ведёт движение.",
    "tips":         "Держи высокий локоть в фазе захвата — он должен быть выше кисти. Финальный толчок — мощный, до бедра.",
    "tags":         ["эспандер", "гребок", "захват", "высокий локоть"],
    "active":       True,
  },
  {
    "title":        "Фонтанчики (flutter kick — сидя)",
    "category":     "freestyle",
    "sub_category": "kick",
    "difficulty":   1,
    "sets":         3,
    "reps":         None,
    "duration_sec": 30,
    "rest_sec":     30,
    "reward_usd":   0.15,
    "input_type":   "done",
    "muscles_primary":    ["квадрицепсы", "сгибатели бедра"],
    "muscles_secondary":  ["передняя большеберцовая мышца"],
    "muscles_stabilizer": ["кор", "подвздошно-поясничная мышца"],
    "swim_benefit": "Поршневой удар ногами генерирует переднюю тягу. Сильные квадрицепсы — высокий ритм ударов от бедра без «тонущих» ног",
    "instructions": "Сесть на край стула или пол, руки упор сзади. Ноги прямые, чуть приподняты. Поочерёдно бить ногами вверх-вниз от бедра — как в кроле. Амплитуда небольшая, ритм частый.",
    "tips":         "Удар идёт от бедра, не от колена. Колени слегка согнуты, не зажаты. Стопы — как ласты, расслаблены.",
    "tags":         ["без инвентаря", "удар ногами", "ритм", "ноги"],
    "active":       True,
  },
  {
    "title":        "Тяга эспандера одной рукой (catch simulation)",
    "category":     "freestyle",
    "sub_category": "pull",
    "difficulty":   2,
    "sets":         3,
    "reps":         10,
    "duration_sec": None,
    "rest_sec":     40,
    "reward_usd":   0.20,
    "input_type":   "reps",
    "muscles_primary":    ["широчайшие мышцы спины", "трицепс"],
    "muscles_secondary":  ["задняя дельта", "большая грудная"],
    "muscles_stabilizer": ["ромбовидные", "кор"],
    "swim_benefit": "Имитирует фазу захвата одной рукой — тренирует симметрию и силу каждого гребка отдельно",
    "instructions": "Стоя, одной рукой тянуть эспандер сверху вниз вдоль тела. Другая рука — вытянута вперёд (имитация второй руки в захвате). По 10 повторений на каждую руку.",
    "tips":         "Не крути корпус. Плечо не поднимай к уху. Следи за симметрией обеих сторон.",
    "tags":         ["эспандер", "симметрия", "одна рука", "захват"],
    "active":       True,
  },

  # ─────────────────────────────────────────────
  # BACKSTROKE — Спина: задняя мышечная цепь
  # Слайд 6 презентации
  # ─────────────────────────────────────────────
  {
    "title":        "Удержание «Супермен»",
    "category":     "backstroke",
    "sub_category": "core",
    "difficulty":   1,
    "sets":         3,
    "reps":         None,
    "duration_sec": 20,
    "rest_sec":     30,
    "reward_usd":   0.15,
    "input_type":   "done",
    "muscles_primary":    ["разгибатели спины", "большая ягодичная мышца"],
    "muscles_secondary":  ["бицепс бедра", "трапеция (нижняя)"],
    "muscles_stabilizer": ["многораздельные мышцы", "кор"],
    "swim_benefit": "Статическое напряжение ягодиц и разгибателей удерживает таз на плаву — тело строго параллельно воде, минимальный угол атаки и сопротивление",
    "instructions": "Лечь на живот, руки вытянуты вперёд. Одновременно поднять руки, грудь и ноги от пола. Удерживать 20 сек. Смотреть вниз, не задирать голову.",
    "tips":         "Напряги ягодицы до максимума. Голову не задирай — продолжение позвоночника. Дыши.",
    "tags":         ["без инвентаря", "задняя цепь", "таз", "позиция тела"],
    "active":       True,
  },
  {
    "title":        "Ягодичный мост",
    "category":     "backstroke",
    "sub_category": "strength",
    "difficulty":   1,
    "sets":         3,
    "reps":         15,
    "duration_sec": None,
    "rest_sec":     30,
    "reward_usd":   0.15,
    "input_type":   "reps",
    "muscles_primary":    ["большая ягодичная мышца", "бицепс бедра"],
    "muscles_secondary":  ["разгибатели спины"],
    "muscles_stabilizer": ["кор", "приводящие бедра"],
    "swim_benefit": "Усиливает статическое напряжение ягодиц — в плавании на спине удерживает бёдра высоко у поверхности воды",
    "instructions": "Лечь на спину, колени согнуты, стопы на полу. Поднять таз вверх до прямой линии плечи-бёдра-колени. Сжать ягодицы в верхней точке на 2 сек. Опустить.",
    "tips":         "Не прогибай поясницу в верхней точке. Стопы на ширине бёдер. Сжимай ягодицы как можно сильнее.",
    "tags":         ["без инвентаря", "ягодицы", "задняя цепь", "базовое"],
    "active":       True,
  },
  {
    "title":        "Тяга эспандера назад (backstroke pull)",
    "category":     "backstroke",
    "sub_category": "pull",
    "difficulty":   2,
    "sets":         3,
    "reps":         12,
    "duration_sec": None,
    "rest_sec":     45,
    "reward_usd":   0.25,
    "input_type":   "reps",
    "muscles_primary":    ["широчайшие мышцы спины", "задняя дельта"],
    "muscles_secondary":  ["трицепс", "ромбовидные"],
    "muscles_stabilizer": ["трапеция", "кор"],
    "swim_benefit": "Имитирует тягу руки в плавании на спине — широчайшие тянут тело вперёд, задняя дельта стабилизирует плечо",
    "instructions": "Стоя спиной к точке крепления эспандера, рука вытянута назад-вверх. Тянуть вдоль тела вниз и к бедру, имитируя гребок на спине. По 12 повторений на каждую руку.",
    "tips":         "Плечо не уводи вперёд. Тяга идёт прямо вдоль тела. Контролируй возврат руки.",
    "tags":         ["эспандер", "гребок", "одна рука"],
    "active":       True,
  },

  # ─────────────────────────────────────────────
  # BREASTSTROKE — Брасс: взрывной хлыст
  # Слайд 7 презентации
  # ─────────────────────────────────────────────
  {
    "title":        "Сед брассиста + имитация удара",
    "category":     "breaststroke",
    "sub_category": "kick",
    "difficulty":   2,
    "sets":         3,
    "reps":         10,
    "duration_sec": None,
    "rest_sec":     45,
    "reward_usd":   0.25,
    "input_type":   "reps",
    "muscles_primary":    ["приводящие мышцы бедра", "квадрицепсы"],
    "muscles_secondary":  ["икроножные мышцы"],
    "muscles_stabilizer": ["кор", "подвздошно-поясничная"],
    "swim_benefit": "Взрывное сведение ног — эффект хлыста в брассе. Растяжка голеностопа (45°) обеспечивает захват воды голенью",
    "instructions": "Сесть на пол, ноги согнуты в коленях и разведены («сед брассиста»). Медленно свести ноги вместе — имитация толчка в брассе. Затем снова развести. 10 повторений.",
    "tips":         "Толчок делай взрывным — это главное. Возврат медленный. Стопы тяни на себя при разведении (как в воде).",
    "tags":         ["без инвентаря", "удар ногами", "взрывной", "сведение ног"],
    "active":       True,
  },
  {
    "title":        "Разведение ног с резиной (лёжа)",
    "category":     "breaststroke",
    "sub_category": "kick",
    "difficulty":   2,
    "sets":         3,
    "reps":         12,
    "duration_sec": None,
    "rest_sec":     40,
    "reward_usd":   0.20,
    "input_type":   "reps",
    "muscles_primary":    ["приводящие мышцы бедра"],
    "muscles_secondary":  ["отводящие мышцы бедра", "квадрицепсы"],
    "muscles_stabilizer": ["кор"],
    "swim_benefit": "Изолированная сила сведения и разведения бёдер — основная пропульсивная фаза брасса, захват воды ногами",
    "instructions": "Лечь на спину, резинка на щиколотках. Ноги чуть согнуты, развести в стороны с усилием против резинки, затем взрывом свести обратно.",
    "tips":         "Взрыв при сведении — это фаза толчка в брассе. При разведении — сопротивляйся резинке медленно.",
    "tags":         ["резинка", "приводящие", "изоляция", "удар брасс"],
    "active":       True,
  },
  {
    "title":        "Приседания с выпрыгиванием (squat jump)",
    "category":     "breaststroke",
    "sub_category": "strength",
    "difficulty":   2,
    "sets":         3,
    "reps":         8,
    "duration_sec": None,
    "rest_sec":     60,
    "reward_usd":   0.25,
    "input_type":   "reps",
    "muscles_primary":    ["квадрицепсы", "большая ягодичная мышца"],
    "muscles_secondary":  ["бицепс бедра", "икроножные"],
    "muscles_stabilizer": ["кор", "приводящие бедра"],
    "swim_benefit": "Взрывная сила разгибания ног — мощный толчок от стенки бассейна и старт с тумбочки в брассе",
    "instructions": "Ноги на ширине плеч. Присесть до параллели бёдер с полом, затем взрывно выпрыгнуть вверх. Приземляться мягко на носки, сразу уходить в следующее приседание.",
    "tips":         "Колени не заваливай внутрь при приземлении. Руки помогают замахом вниз-вверх.",
    "tags":         ["без инвентаря", "взрывной", "прыжок", "толчок от стенки"],
    "active":       True,
  },

  # ─────────────────────────────────────────────
  # BUTTERFLY — Баттерфляй: кинетическая волна
  # Слайд 8 презентации
  # ─────────────────────────────────────────────
  {
    "title":        "Выпрыгивания с броском медбола",
    "category":     "butterfly",
    "sub_category": "kick",
    "difficulty":   3,
    "sets":         3,
    "reps":         8,
    "duration_sec": None,
    "rest_sec":     60,
    "reward_usd":   0.35,
    "input_type":   "reps",
    "muscles_primary":    ["взрывная сила ног (квадрицепс, ягодицы)", "мышцы кора"],
    "muscles_secondary":  ["дельтовидные", "трапеция"],
    "muscles_stabilizer": ["разгибатели спины", "поперечная мышца живота"],
    "swim_benefit": "Генерация волнового импульса: энергия от бёдер → через жёсткий корсет → плечевой пояс. Основа дельфиньего удара и мощного выхода со старта",
    "instructions": "Держать медбол (1–2 кг) у груди. Присесть, затем взрывно выпрыгнуть, бросая мяч вверх над головой. Поймать, приземлиться мягко. Вся цепочка — одно слитное движение.",
    "tips":         "Бросок идёт от ног, не от рук. Почувствуй как энергия проходит снизу вверх через всё тело — это и есть волна баттерфляя.",
    "tags":         ["медбол", "взрывной", "кинетическая цепь", "волна", "старт"],
    "active":       True,
  },
  {
    "title":        "Волна дельфина (dolphin kick — на полу)",
    "category":     "butterfly",
    "sub_category": "kick",
    "difficulty":   2,
    "sets":         3,
    "reps":         10,
    "duration_sec": None,
    "rest_sec":     45,
    "reward_usd":   0.25,
    "input_type":   "reps",
    "muscles_primary":    ["кор / пресс", "бёдра и ягодицы"],
    "muscles_secondary":  ["дельтовидные", "икроножные"],
    "muscles_stabilizer": ["трапеция", "разгибатели спины"],
    "swim_benefit": "Волнообразное движение от груди — передаёт импульс через всё тело. Дельфиний удар = главная тяга баттерфляя",
    "instructions": "Лечь на живот, руки вытянуты над головой. Выполнять волнообразные движения всем телом от груди до кончиков ног. Волна идёт сверху вниз: грудь → бёдра → ноги.",
    "tips":         "Движение начинается от корпуса, НЕ от колен. Держи колени чуть согнутыми. Не делай слишком большую амплитуду.",
    "tags":         ["без инвентаря", "волна", "дельфин", "техника"],
    "active":       True,
  },
  {
    "title":        "Отжимания широким хватом",
    "category":     "butterfly",
    "sub_category": "arms",
    "difficulty":   2,
    "sets":         3,
    "reps":         10,
    "duration_sec": None,
    "rest_sec":     45,
    "reward_usd":   0.20,
    "input_type":   "reps",
    "muscles_primary":    ["большая грудная", "трицепс"],
    "muscles_secondary":  ["передняя дельта", "передняя зубчатая"],
    "muscles_stabilizer": ["кор", "ромбовидные"],
    "swim_benefit": "Мощный вынос рук вперёд и гребок в баттерфляе — одновременный симметричный толчок обеими руками",
    "instructions": "Упор лёжа, руки шире плеч. Опуститься грудью к полу, затем взрывно отжаться. В верхней точке — полное выпрямление рук.",
    "tips":         "Держи тело прямым как доска (кор). Локти под углом ~45° к телу, не разводи в стороны.",
    "tags":         ["без инвентаря", "симметрия", "толчок", "руки"],
    "active":       True,
  },
  {
    "title":        "Ягодичный мост с волной (glute bridge wave)",
    "category":     "butterfly",
    "sub_category": "core",
    "difficulty":   2,
    "sets":         3,
    "reps":         10,
    "duration_sec": None,
    "rest_sec":     40,
    "reward_usd":   0.20,
    "input_type":   "reps",
    "muscles_primary":    ["большая ягодичная мышца", "кор / пресс"],
    "muscles_secondary":  ["бицепс бедра", "разгибатели спины"],
    "muscles_stabilizer": ["поперечная мышца живота"],
    "swim_benefit": "Тренирует последовательную активацию мышц от бёдер вверх — точная копия механики дельфиньего удара лёжа",
    "instructions": "Лечь на спину, колени согнуты. Медленно поднять таз, затем грудной отдел, затем плечи — волнообразно. Опускать в обратном порядке.",
    "tips":         "Движение плавное, как волна. Каждый позвонок поднимается и опускается по очереди.",
    "tags":         ["без инвентаря", "волна", "последовательная активация", "кор"],
    "active":       True,
  },
]

# ─────────────────────────────────────────────────────────────
# Расписания по умолчанию
# ─────────────────────────────────────────────────────────────
# Логика: упражнения группируются по дням недели
# Пн/Чт  — Кроль + База
# Вт/Пт  — Спина + Брасс
# Ср/Сб  — Баттерфляй + База

DEFAULT_SCHEDULES = [
    # category        sub   дни              время
    ("universal",     None, ["mon","thu"],   "17:00"),
    ("freestyle",     None, ["mon","thu"],   "17:00"),
    ("backstroke",    None, ["tue","fri"],   "17:00"),
    ("breaststroke",  None, ["tue","fri"],   "17:00"),
    ("butterfly",     None, ["wed","sat"],   "17:00"),
    ("universal",     None, ["wed","sat"],   "17:00"),
]

# ─────────────────────────────────────────────────────────────

def get_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def seed():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    db = get_db(DB_PATH)

    # Check table exists
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "exercises" not in tables:
        print("ERROR: таблицы не найдены. Сначала запусти приложение (docker-compose up -d --build), потом сидер.")
        sys.exit(1)

    existing = db.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    if existing > 0:
        answer = input(f"В базе уже {existing} упражнений. Добавить ещё? (y/n): ").strip().lower()
        if answer != "y":
            print("Отмена.")
            sys.exit(0)

    inserted_ids = {}  # title -> id

    print(f"\nДобавляю {len(EXERCISES)} упражнений...\n")
    for ex in EXERCISES:
        tags_json = json.dumps(ex.get("tags", []), ensure_ascii=False)
        try:
            cur = db.execute("""
                INSERT INTO exercises (
                    title, category, sub_category, difficulty,
                    sets, reps, duration_sec, rest_sec,
                    reward_usd, input_type,
                    muscles_primary, muscles_secondary, muscles_stabilizer,
                    swim_benefit, instructions, tips, active
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                ex["title"], ex["category"], ex["sub_category"], ex["difficulty"],
                ex["sets"], ex.get("reps"), ex.get("duration_sec"), ex["rest_sec"],
                ex["reward_usd"], ex["input_type"],
                json.dumps(ex["muscles_primary"],    ensure_ascii=False),
                json.dumps(ex["muscles_secondary"],  ensure_ascii=False),
                json.dumps(ex["muscles_stabilizer"], ensure_ascii=False),
                ex["swim_benefit"], ex["instructions"], ex["tips"], int(ex["active"])
            ))
            ex_id = cur.lastrowid
            inserted_ids[ex["title"]] = ex_id
            cat_emoji = {"universal":"🏋️","freestyle":"🏊","backstroke":"🔄","breaststroke":"🐸","butterfly":"🦋"}.get(ex["category"],"•")
            diff_str  = "★" * ex["difficulty"] + "☆" * (3 - ex["difficulty"])
            dur_str   = f"{ex['duration_sec']}сек" if ex.get("duration_sec") else f"{ex['reps']} повт."
            print(f"  {cat_emoji} [{ex_id:2d}] {ex['title'][:45]:<45} {diff_str}  {ex['sets']}×{dur_str}  ${ex['reward_usd']:.2f}")
        except Exception as e:
            print(f"  ✗ ОШИБКА: {ex['title']}: {e}")

    db.commit()

    # Add schedules
    print(f"\nНастраиваю расписание...")
    existing_schedules = db.execute("SELECT COUNT(*) FROM schedules").fetchone()[0]
    if existing_schedules == 0:
        for cat, sub, days, time in DEFAULT_SCHEDULES:
            ex_rows = db.execute(
                "SELECT id FROM exercises WHERE category=? AND active=1 ORDER BY difficulty, id",
                (cat,)
            ).fetchall()
            for row in ex_rows:
                db.execute(
                    "INSERT INTO schedules (exercise_id, frequency, days, notify_time, active) VALUES (?,?,?,?,1)",
                    (row["id"], "custom", json.dumps(days), time)
                )
        db.commit()
        print(f"  Расписание создано:")
        print(f"  Пн/Чт 17:00 — Кроль + База")
        print(f"  Вт/Пт 17:00 — Спина + Брасс")
        print(f"  Ср/Сб 17:00 — Баттерфляй + База")
    else:
        print(f"  Расписание уже существует ({existing_schedules} записей), пропускаю.")

    db.close()

    total = len(inserted_ids)
    total_reward = sum(ex["reward_usd"] for ex in EXERCISES)
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Готово! Добавлено {total} упражнений
  Суммарная награда за всё: ${total_reward:.2f}

  Категории:
  🏋️  База/Универсальные: {sum(1 for e in EXERCISES if e['category']=='universal')}
  🏊  Кроль (Freestyle):  {sum(1 for e in EXERCISES if e['category']=='freestyle')}
  🔄  Спина (Backstroke): {sum(1 for e in EXERCISES if e['category']=='backstroke')}
  🐸  Брасс:             {sum(1 for e in EXERCISES if e['category']=='breaststroke')}
  🦋  Баттерфляй:        {sum(1 for e in EXERCISES if e['category']=='butterfly')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

if __name__ == "__main__":
    seed()
