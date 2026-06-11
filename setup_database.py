import sqlite3
import os

# Create database in same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fantasy_cricket.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ── Table 1: stats (player profiles) ──────────────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    player  TEXT PRIMARY KEY,
    matches INTEGER,
    runs    INTEGER,
    hundreds INTEGER,
    fifties  INTEGER,
    value   INTEGER,
    ctg     TEXT
)
""")

# ── Table 2: match (per-match performance data) ────────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS match (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    player  TEXT,
    match_name TEXT,
    scored  INTEGER DEFAULT 0,
    faced   INTEGER DEFAULT 0,
    fours   INTEGER DEFAULT 0,
    sixes   INTEGER DEFAULT 0,
    bowled  INTEGER DEFAULT 0,
    maiden  INTEGER DEFAULT 0,
    given   INTEGER DEFAULT 0,
    wkts    INTEGER DEFAULT 0,
    catches INTEGER DEFAULT 0,
    stumping INTEGER DEFAULT 0,
    run_out  INTEGER DEFAULT 0
)
""")

# ── Table 3: teams (saved teams after score evaluation) ────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    name    TEXT PRIMARY KEY,
    players TEXT,
    value   INTEGER
)
""")

# ── Seed data: stats table ─────────────────────────────────────────────────────
players = [
    # (player, matches, runs, 100s, 50s, value, category)
    # Batsmen
    ("Virat Kohli",     250, 12000, 43, 65, 10, "Batsman"),
    ("Rohit Sharma",    240, 10500, 30, 48, 9,  "Batsman"),
    ("Shubman Gill",    80,  3200,  8,  18, 7,  "Batsman"),
    ("KL Rahul",        150, 6000,  18, 32, 8,  "Batsman"),
    ("Shreyas Iyer",    120, 4500,  10, 25, 7,  "Batsman"),
    ("Sanju Samson",    100, 3800,  6,  20, 6,  "Batsman"),
    # Bowlers
    ("Jasprit Bumrah",  130, 400,   0,  0,  10, "Bowler"),
    ("Mohammed Shami",  120, 380,   0,  0,  9,  "Bowler"),
    ("Ravindra Jadeja", 200, 2500,  3,  15, 9,  "Bowler"),
    ("Kuldeep Yadav",   100, 300,   0,  0,  8,  "Bowler"),
    ("Yuzvendra Chahal",110, 280,   0,  0,  7,  "Bowler"),
    ("Mohammed Siraj",  90,  250,   0,  0,  7,  "Bowler"),
    # All-rounders
    ("Hardik Pandya",   180, 3500,  2,  22, 9,  "All-Rounder"),
    ("Axar Patel",      130, 1800,  1,  10, 8,  "All-Rounder"),
    ("Washington Sundar",80, 900,   0,  5,  7,  "All-Rounder"),
    ("Shardul Thakur",  100, 1200,  0,  8,  7,  "All-Rounder"),
    # Wicket-keepers
    ("MS Dhoni",        350, 10500, 10, 73, 10, "Wicket-Keeper"),
    ("Rishabh Pant",    120, 4200,  6,  24, 9,  "Wicket-Keeper"),
    ("Ishan Kishan",    80,  2800,  3,  15, 7,  "Wicket-Keeper"),
    ("Dinesh Karthik",  150, 3600,  0,  18, 6,  "Wicket-Keeper"),
]

cursor.executemany("""
    INSERT OR IGNORE INTO stats (player, matches, runs, hundreds, fifties, value, ctg)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", players)

# ── Seed data: match table (3 matches with realistic stats) ────────────────────
match_data = [
    # Match 1: IND vs AUS
    ("Virat Kohli",      "IND vs AUS", 82, 90,  8, 2, 0, 0, 0,  0, 1, 0, 0),
    ("Rohit Sharma",     "IND vs AUS", 56, 48,  6, 3, 0, 0, 0,  0, 0, 0, 1),
    ("Shubman Gill",     "IND vs AUS", 34, 42,  3, 1, 0, 0, 0,  0, 2, 0, 0),
    ("KL Rahul",         "IND vs AUS", 45, 55,  4, 1, 0, 0, 0,  0, 1, 1, 0),
    ("Shreyas Iyer",     "IND vs AUS", 28, 30,  2, 1, 0, 0, 0,  0, 0, 0, 0),
    ("Sanju Samson",     "IND vs AUS", 18, 22,  1, 0, 0, 0, 0,  0, 1, 0, 0),
    ("Jasprit Bumrah",   "IND vs AUS", 4,  12,  0, 0, 8, 1, 24, 3, 0, 0, 1),
    ("Mohammed Shami",   "IND vs AUS", 2,  6,   0, 0, 7, 0, 32, 2, 1, 0, 0),
    ("Ravindra Jadeja",  "IND vs AUS", 22, 28,  1, 0, 6, 1, 22, 2, 2, 0, 0),
    ("Kuldeep Yadav",    "IND vs AUS", 0,  4,   0, 0, 7, 0, 28, 2, 0, 0, 0),
    ("Yuzvendra Chahal", "IND vs AUS", 0,  2,   0, 0, 6, 0, 30, 1, 1, 0, 0),
    ("Mohammed Siraj",   "IND vs AUS", 0,  4,   0, 0, 5, 0, 25, 1, 0, 0, 0),
    ("Hardik Pandya",    "IND vs AUS", 38, 32,  3, 2, 4, 0, 18, 2, 1, 0, 0),
    ("Axar Patel",       "IND vs AUS", 15, 20,  1, 0, 5, 1, 20, 1, 2, 0, 0),
    ("Washington Sundar","IND vs AUS", 12, 18,  0, 0, 4, 0, 22, 1, 0, 0, 1),
    ("Shardul Thakur",   "IND vs AUS", 20, 25,  2, 0, 5, 0, 28, 1, 1, 0, 0),
    ("MS Dhoni",         "IND vs AUS", 30, 20,  2, 2, 0, 0, 0,  0, 1, 2, 0),
    ("Rishabh Pant",     "IND vs AUS", 48, 40,  4, 3, 0, 0, 0,  0, 2, 1, 0),
    ("Ishan Kishan",     "IND vs AUS", 22, 25,  1, 1, 0, 0, 0,  0, 1, 0, 0),
    ("Dinesh Karthik",   "IND vs AUS", 15, 10,  1, 2, 0, 0, 0,  0, 2, 1, 0),

    # Match 2: IND vs ENG
    ("Virat Kohli",      "IND vs ENG", 102,115, 10,3, 0, 0, 0,  0, 0, 0, 0),
    ("Rohit Sharma",     "IND vs ENG", 35, 40,  3, 1, 0, 0, 0,  0, 1, 0, 0),
    ("Shubman Gill",     "IND vs ENG", 65, 72,  7, 2, 0, 0, 0,  0, 1, 0, 1),
    ("KL Rahul",         "IND vs ENG", 20, 28,  2, 0, 0, 0, 0,  0, 0, 1, 0),
    ("Shreyas Iyer",     "IND vs ENG", 55, 60,  5, 2, 0, 0, 0,  0, 2, 0, 0),
    ("Sanju Samson",     "IND vs ENG", 42, 38,  3, 3, 0, 0, 0,  0, 0, 0, 1),
    ("Jasprit Bumrah",   "IND vs ENG", 0,  8,   0, 0, 9, 2, 18, 5, 1, 0, 0),
    ("Mohammed Shami",   "IND vs ENG", 0,  5,   0, 0, 8, 1, 22, 3, 0, 0, 0),
    ("Ravindra Jadeja",  "IND vs ENG", 30, 35,  2, 0, 7, 1, 25, 2, 1, 0, 0),
    ("Kuldeep Yadav",    "IND vs ENG", 0,  3,   0, 0, 8, 0, 24, 3, 2, 0, 0),
    ("Yuzvendra Chahal", "IND vs ENG", 0,  2,   0, 0, 7, 0, 20, 2, 0, 0, 0),
    ("Mohammed Siraj",   "IND vs ENG", 0,  4,   0, 0, 6, 0, 30, 1, 1, 0, 0),
    ("Hardik Pandya",    "IND vs ENG", 52, 42,  4, 3, 5, 0, 22, 2, 0, 0, 1),
    ("Axar Patel",       "IND vs ENG", 20, 25,  1, 0, 6, 1, 18, 2, 1, 0, 0),
    ("Washington Sundar","IND vs ENG", 8,  12,  0, 0, 5, 0, 20, 1, 2, 0, 0),
    ("Shardul Thakur",   "IND vs ENG", 14, 18,  1, 0, 6, 0, 32, 2, 0, 0, 0),
    ("MS Dhoni",         "IND vs ENG", 22, 15,  1, 1, 0, 0, 0,  0, 3, 1, 0),
    ("Rishabh Pant",     "IND vs ENG", 58, 50,  5, 4, 0, 0, 0,  0, 1, 2, 0),
    ("Ishan Kishan",     "IND vs ENG", 30, 32,  2, 1, 0, 0, 0,  0, 2, 0, 1),
    ("Dinesh Karthik",   "IND vs ENG", 10, 8,   0, 1, 0, 0, 0,  0, 1, 2, 0),

    # Match 3: IND vs SA
    ("Virat Kohli",      "IND vs SA",  44, 52,  4, 1, 0, 0, 0,  0, 1, 0, 0),
    ("Rohit Sharma",     "IND vs SA",  78, 68,  8, 4, 0, 0, 0,  0, 0, 0, 0),
    ("Shubman Gill",     "IND vs SA",  22, 30,  2, 0, 0, 0, 0,  0, 0, 0, 1),
    ("KL Rahul",         "IND vs SA",  90, 95,  9, 2, 0, 0, 0,  0, 2, 0, 0),
    ("Shreyas Iyer",     "IND vs SA",  12, 18,  1, 0, 0, 0, 0,  0, 1, 0, 0),
    ("Sanju Samson",     "IND vs SA",  60, 55,  6, 3, 0, 0, 0,  0, 0, 0, 0),
    ("Jasprit Bumrah",   "IND vs SA",  6,  10,  0, 0, 7, 1, 20, 2, 0, 0, 0),
    ("Mohammed Shami",   "IND vs SA",  0,  4,   0, 0, 6, 0, 28, 2, 1, 0, 1),
    ("Ravindra Jadeja",  "IND vs SA",  18, 22,  1, 0, 5, 0, 24, 1, 2, 0, 0),
    ("Kuldeep Yadav",    "IND vs SA",  0,  2,   0, 0, 6, 0, 26, 2, 1, 0, 0),
    ("Yuzvendra Chahal", "IND vs SA",  0,  3,   0, 0, 5, 0, 22, 2, 0, 0, 0),
    ("Mohammed Siraj",   "IND vs SA",  2,  6,   0, 0, 7, 1, 22, 3, 0, 0, 0),
    ("Hardik Pandya",    "IND vs SA",  28, 22,  2, 1, 3, 0, 15, 1, 1, 0, 0),
    ("Axar Patel",       "IND vs SA",  10, 15,  0, 0, 4, 0, 18, 1, 0, 0, 1),
    ("Washington Sundar","IND vs SA",  6,  10,  0, 0, 3, 0, 16, 1, 1, 0, 0),
    ("Shardul Thakur",   "IND vs SA",  18, 20,  1, 0, 4, 0, 24, 1, 2, 0, 0),
    ("MS Dhoni",         "IND vs SA",  14, 12,  1, 0, 0, 0, 0,  0, 2, 1, 0),
    ("Rishabh Pant",     "IND vs SA",  36, 30,  3, 2, 0, 0, 0,  0, 1, 1, 0),
    ("Ishan Kishan",     "IND vs SA",  18, 20,  1, 1, 0, 0, 0,  0, 0, 1, 0),
    ("Dinesh Karthik",   "IND vs SA",  8,  6,   0, 1, 0, 0, 0,  0, 1, 0, 1),
]

cursor.executemany("""
    INSERT INTO match
    (player, match_name, scored, faced, fours, sixes,
     bowled, maiden, given, wkts, catches, stumping, run_out)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", match_data)

conn.commit()
conn.close()
print("✅ Database created successfully!")
print(f"📁 Location: {DB_PATH}")
print(f"\nTables created: stats, match, teams")
print(f"Players added: {len(players)}")
print(f"Match records added: {len(match_data)}")
