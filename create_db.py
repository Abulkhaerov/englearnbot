import sqlite3
from config import config
from db import add_to_whitelist, add_admin
from logger import info, warning, error

whitelisted = config['users']['whitelisted']
admins = config['users']['admins']

info("Starting database creation/initialization...")

try:
    conn = sqlite3.connect(config['database']['path'])
    c = conn.cursor()

    info("Creating tables if not exist...")
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY,
                  is_whitelisted BOOLEAN DEFAULT 0, 
                  is_admin BOOLEAN DEFAULT 0,
                  time_joined INTEGER,
                  day_streak INTEGER DEFAULT 0,
                  last_day_solved TEXT DEFAULT NULL,
                  words_for_today TEXT DEFAULT '',
                  words_added_at TEXT DEFAULT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS OXFORD3000
                 (word TEXT PRIMARY KEY, translation TEXT, usage_examples TEXT, complexity_level TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS OXFORD5000
                 (word TEXT PRIMARY KEY, translation TEXT, usage_examples TEXT, complexity_level TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist
                 (id INTEGER PRIMARY KEY, is_whitelisted BOOLEAN DEFAULT 0, is_admin BOOLEAN DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY, word TEXT, wordlist TEXT, translation TEXT, usage_examples TEXT, complexity_level TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
        user_id         BIGINT,
        word_id         INTEGER,
        ease_factor     REAL    DEFAULT 2.5,
        interval_days   INTEGER DEFAULT 1,
        last_review_date TEXT,
        times_seen      INTEGER DEFAULT 0,
        repetitions    INTEGER DEFAULT 0,
        times_correct   INTEGER DEFAULT 0,
        rating_history TEXT DEFAULT '',
        next_review_date TEXT,
        PRIMARY KEY (user_id, word_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (word_id) REFERENCES words(id)
    );''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        user_id         BIGINT,
        active_wordlist TEXT DEFAULT 'OXFORD3000',
        new_words_per_day INTEGER DEFAULT 5,
        debug BOOLEAN DEFAULT 0,
        reminder_time TEXT DEFAULT '15:00',
        PRIMARY KEY (user_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );''')

    conn.commit()
    info("Tables created/verified successfully.")

    info(f"Adding {len(admins)} admins and {len(whitelisted)} whitelisted users...")
    for admin in admins:
        add_admin(admin)
    for person in whitelisted:
        add_to_whitelist(person)
    info("Admins and whitelisted users processed.")

    id = 0
    info("Loading OXFORD5000 wordlist...")
    oxford5k = open(config['wordlists']['oxford_5000'], 'r')
    for line in oxford5k.readlines():
        word = line.strip()
        if word:
            c.execute("INSERT OR IGNORE INTO OXFORD5000 (word) VALUES (?)", (word,))
            c.execute("INSERT OR IGNORE INTO words (id, word, wordlist) VALUES (?,?,?)", (id, word, "OXFORD5000"))
            id += 1
    oxford5k.close()

    info("Loading OXFORD3000 wordlist...")
    oxford3k = open(config['wordlists']['oxford_3000'], 'r')
    for line in oxford3k.readlines():
        word = line.strip()
        if word:
            c.execute("INSERT OR IGNORE INTO OXFORD3000 (word) VALUES (?)", (word,))
            c.execute("INSERT OR IGNORE INTO words (id, word, wordlist) VALUES (?,?,?)", (id, word, "OXFORD3000"))
            id += 1
    oxford3k.close()

    conn.commit()
    conn.close()
    info(f"Database initialization completed successfully. Total words inserted: {id}")

except Exception as e:
    error(f"Error during database creation: {e}")
    raise