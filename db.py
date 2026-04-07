import sqlite3
from config import config
import asyncio
from datetime import date, timedelta
from logger import info, warning, error, debug
import random

conn = sqlite3.connect(config['database']['path'], check_same_thread=False, timeout=7)
conn.execute("PRAGMA journal_mode=WAL;")
c = conn.cursor()
conn.execute("PRAGMA foreign_keys = ON;")
from utils import SM2

def add_user(id):#todo fix bug here
    info(f"Adding new user: {id}")
    try:
        c.execute("SELECT * FROM whitelist WHERE id=?", (id,))
        res=c.fetchone()
        is_whitelisted=0
        is_admin=0
        if res is not None:
            is_whitelisted=int(res[1])
            is_admin=int(res[2])
        else:
            c.execute("INSERT OR IGNORE INTO whitelist (id) VALUES (?)",
                      (id,))

        c.execute("INSERT OR IGNORE INTO users (user_id, is_whitelisted, is_admin) VALUES (?, ?, ?)", (id,is_whitelisted,is_admin,))
        c.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)",
                  (id,))
        conn.commit()
        info(f"User {id} added successfully")
    except Exception as e:
        conn.rollback()
        error(f"Failed to add user {id}: {e}")

def is_added_to_users(id):
    info(f"Checking if user {id} is added to users table")
    try:
        c.execute("SELECT * FROM users WHERE user_id=?", (id,))
        res=c.fetchone()
        if res is not None:
            info(f"User {id} is added to users table")
            return True
        else:
            info(f"User {id} is not added to users table")
            return False
    except Exception as e:
        conn.rollback()
        error(f"Failed to check if user {id} is added to users table: {e}")


def is_admin(id):
    info(f"Checking if user {id} is admin")
    try:
        c.execute("SELECT * FROM whitelist WHERE id=?", (id,))
        res=c.fetchone()
        if res is None:
            info(f"User {id} is not admin")
            return False
        else:
            if res[2] == 1:
                info(f"User {id} is admin")
                return True
            else:
                info(f"User {id} is not admin")
                return False
    except Exception as e:
        error(f"Failed to check if user {id} is admin: {e}")

def is_whitelisted(id):
    info(f"Checking if user {id} is whitelisted")
    try:
        c.execute("SELECT * FROM whitelist WHERE id=?", (id,))
        res=c.fetchone()
        if res is None:
            info(f"User {id} is not whitelisted")
            return False
        else:
            if res[1] == 1:
                info(f"User {id} is whitelisted")
                return True
            else:
                info(f"User {id} is not whitelisted")
                return False
    except Exception as e:
        conn.rollback()
        error(f"Failed to check if user {id} is whitelisted: {e}")
def add_admin(id):
    info(f"Adding/updating admin: {id}")
    try:
        c.execute("SELECT * FROM whitelist where id=(?)", (id,))
        if c.fetchone() is None:
            c.execute("INSERT INTO whitelist (id, is_admin) VALUES (?, True)", (id,))
        else:
            c.execute("UPDATE whitelist SET is_admin=1 WHERE id=?", (id,))
        conn.commit()
        info(f"Admin {id} processed")
    except Exception as e:
        error(f"Failed to add admin {id}: {e}")

def add_to_whitelist(id):
    info(f"Adding/updating whitelisted user: {id}")
    try:
        c.execute("SELECT * FROM whitelist where id=(?)", (id,))
        if c.fetchone() is None:
            c.execute("INSERT INTO whitelist (id, is_whitelisted) VALUES (?,True)", (id,))
        else:
            c.execute("UPDATE whitelist SET is_whitelisted=1 WHERE id=?", (id,))
        conn.commit()
        info(f"Whitelisted user {id} processed")
    except Exception as e:
        error(f"Failed to whitelist user {id}: {e}")

def get_whitelisted_users():
    info("Getting whitelisted users list")
    try:
        c.execute("SELECT * FROM whitelist")
        res=c.fetchall()
        if res is None:
            return []
        else:
            result=[]
            for usr in res:
                if usr[1]==1:
                    #whitelisted
                    result.append(usr[0])
            return result
    except Exception as e:
        error(f"Failed to get whitelist: {e}")

def add_progress(user_id, word_id, result):
    info(f"Recording progress: user={user_id}, word_id={word_id}, rating={result}")
    today = date.today()
    today_str = today.isoformat()

    try:
        c.execute("SELECT * FROM user_progress where (user_id, word_id)=(?,?)", (user_id, word_id))
        if c.fetchone() is None:
            info(f"New progress entry for user {user_id}, word {word_id}")
            c.execute("INSERT INTO user_progress (user_id, word_id) VALUES (?,?)", (user_id, word_id))
            conn.commit()

        c.execute("SELECT * FROM user_progress where (user_id, word_id)=(?,?)", (user_id, word_id))
        res = c.fetchone()
        if not res:
            error(f"Failed to fetch progress after insert for user {user_id}, word {word_id}")
            return

        interval = res[3]
        repetitions = res[6]
        ease_factor = res[2]
        times_seen = res[5] + 1
        times_correct = res[7] + (1 if result >= 3 else 0)
        rating_history = (res[8] or "") + str(result)

        debug(f"Current state: interval={interval}, reps={repetitions}, ease={ease_factor:.3f}, seen={times_seen}, correct={times_correct}")

        new_interval, new_repetitions, new_ease_factor = SM2(result, repetitions, ease_factor, interval)
        next_review_date_str = (today + timedelta(days=new_interval)).isoformat()

        c.execute('''UPDATE user_progress 
                     SET last_review_date = ?,
                     interval_days = ?,
                     ease_factor = ?,
                     repetitions = ?,   
                     times_seen = ?,
                     times_correct = ?,
                     rating_history = ?,
                     next_review_date = ?
                     WHERE user_id = ? AND word_id = ?''',
                  (today_str, new_interval, new_ease_factor, new_repetitions,
                   times_seen, times_correct, rating_history, next_review_date_str,
                   user_id, word_id))

        conn.commit()
        info(f"Progress updated successfully: next review in {new_interval} days, ease={new_ease_factor:.3f}")

    except Exception as e:
        error(f"Error updating progress for user {user_id}, word {word_id}: {e}")
        conn.rollback()


def words_for_today(user_id):
    today = date.today()
    today_str = today.isoformat()

    info(f"Calculating words_for_today for user {user_id} on {today_str}")

    c.execute("""
        SELECT word_id 
        FROM user_progress 
        WHERE user_id = ? AND next_review_date <= ?
    """, (user_id, today_str,))
    review_words = [row[0] for row in c.fetchall()]
    info(f"Found {len(review_words)} words due for review today")

    c.execute("SELECT active_wordlist, new_words_per_day FROM user_settings WHERE user_id = ?", (user_id,))
    settings = c.fetchone()

    if not settings:
        error(f"No settings found for user {user_id} – cannot determine wordlist or new words limit")
        return review_words

    active_wordlist, new_words_per_day = settings
    info(f"User {user_id} settings: wordlist='{active_wordlist}', new_words_per_day={new_words_per_day}")

    new_words = []

    if active_wordlist == "OXFORD3000":
        source_table = "OXFORD3000"
    elif active_wordlist == "OXFORD5000":
        source_table = "OXFORD5000"
    else:
        error(f"Unknown wordlist '{active_wordlist}' for user {user_id}")
        return review_words

    #some magic here
    c.execute('''
        SELECT w.id 
        FROM words w
        LEFT JOIN user_progress up ON w.id = up.word_id AND up.user_id = ?
        WHERE w.wordlist = ? AND up.word_id IS NULL
    ''', (user_id, active_wordlist))

    unseen_word_ids = [row[0] for row in c.fetchall()]
    total_unseen = len(unseen_word_ids)

    info(f"Found {total_unseen} unseen words in {active_wordlist} for user {user_id}")

    if total_unseen == 0:
        info(f"No new words available – user {user_id} has seen all words in {active_wordlist}")
    else:
        if total_unseen < new_words_per_day:
            warning(f"Only {total_unseen} unseen words left (requested {new_words_per_day}) for user {user_id}")
            selected_new = unseen_word_ids
        else:
            selected_new = random.sample(unseen_word_ids, new_words_per_day)

        new_words = selected_new
        info(f"Selected {len(new_words)} new words for today")

    all_words_today = review_words + new_words
    random.shuffle(all_words_today)
    info(f"Total words for today: {len(all_words_today)} ({len(review_words)} reviews + {len(new_words)} new)")

    info(f"Saving {len(all_words_today)} words for today for user {user_id}")

    words_str = ';'.join(map(str, all_words_today))  # Safe conversion

    try:
        c.execute('''UPDATE users
                     SET words_for_today = ?,
                         words_added_at = ?
                     WHERE user_id = ?''',
                  (words_str, today_str, user_id))
        conn.commit()
        info(f"Successfully saved today's words and set words_added_at = {today_str} for user {user_id}")
    except Exception as e:
        error(f"Failed to save today's words for user {user_id}: {e}")
        conn.rollback()

    return all_words_today


def are_words_up_to_date(user_id):
    today = date.today()
    today_str = today.isoformat()
    info(f"Checking if words are up to date for user {user_id} (today: {today_str})")
    try:
        c.execute("""
            SELECT words_added_at 
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        row = c.fetchone()
        if row is None:
            warning(f"No user record found for user_id {user_id}")
            return False
        stored_date = row[0]
        is_up_to_date = (stored_date == today_str)
        info(f"words_added_at = '{stored_date}' → up to date: {is_up_to_date}")
        return is_up_to_date
    except Exception as e:
        error(f"Error checking words_up_to_date for user {user_id}: {e}")
        return False


def get_word_for_today(user_id):
    info(f"Requesting next word for today for user {user_id}")
    try:
        c.execute("""
            SELECT words_for_today 
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        row = c.fetchone()
        if row is None:
            error(f"No user record found for user_id {user_id}")
            return None
        words_str = row[0]
        if not words_str:
            info(f"No words left today for user {user_id} (words_for_today is empty)")
            return None
        words = words_str.split(';')
        info(f"Loaded {len(words)} words from words_for_today for user {user_id}")
        word_id_str = words.pop()
        word_id = int(word_id_str)
        info(f"Serving word_id {word_id} to user {user_id}")
        new_words_str = ';'.join(words)
        c.execute('''UPDATE users
                     SET words_for_today = ?
                     WHERE user_id = ?''', (new_words_str, user_id))
        conn.commit()
        info(f"Updated words_for_today: {len(words)} words remaining for user {user_id}")
        return word_id
    except ValueError:
        error(f"Invalid word ID in words_for_today string for user {user_id}: '{word_id_str}'")
        return None
    except Exception as e:
        error(f"Error in get_word_for_today for user {user_id}: {e}")
        conn.rollback()
        return None


def get_word_info(word_id):
    info(f"Fetching word info for word_id={word_id}")

    try:
        c.execute("SELECT * FROM words WHERE id = ?", (word_id,))
        row = c.fetchone()

        if row is None:
            warning(f"Word with id={word_id} not found in 'words' table")
            return None

        if len(row) < 6:
            error(f"Incomplete row data for word_id={word_id}: got {len(row)} columns, expected at least 6")
            return None

        res = {
            "id": word_id,
            "word": row[1],
            "wordlist": row[2],
            "translation": row[3] or "",
            "usage_examples": row[4] or "",
            "complexity_level": row[5] or ""
        }

        info(f"Successfully retrieved word info: '{res['word']}' (wordlist: {res['wordlist']})")
        return res

    except Exception as e:
        error(f"Error fetching word info for word_id={word_id}: {e}")
        return None

def update_word_info(word_id, word_info:dict):
    info(f"Updating word info for word_id={word_id}")
    try:
        for setting, new_info in word_info.items():
            info(f"Updating word info for word_id={word_id}: '{setting}':'{new_info}'")
            # Dynamically include the column name using string formatting
            query = f"UPDATE words SET {setting} = ? WHERE id = ?"
            c.execute(query, (new_info, word_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        error(f"Error updating word info for word_id={word_id}: {e}")

def get_settings(user_id):
    info(f"Fetching settings for user {user_id}")
    try:
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            warning(f"No user record found for user_id {user_id}")
            return None
        if len(row) < 4:
            error(f"Incomplete row data for user_id={user_id}: got {len(row)} columns, expected at least 4")
            return None
        res = {
            "user_id": user_id,
            "active_wordlist": row[1],
            "new_words_per_day": row[2],
            "debug": row[3],
            "reminder_time": row[4]
        }
        info(f"Successfully retrieved settings for user {user_id}(active_wordlist: {res['active_wordlist']}, new_words_per_day: {res['new_words_per_day']}, debug: {res['debug']}, reminder_time:{res['reminder_time']})")
        return res
    except:
        error(f"Error fetching settings for user {user_id}")
        return None

def change_settings(user_id, settigs_update:dict):
    info(f"Changing settings for user {user_id}")

    try:
        for setting, new_value in settigs_update.items():
            info(f"Changing setting '{setting}' to '{new_value}' for user {user_id}")
            query = f"UPDATE user_settings SET {setting} = ? WHERE user_id = ?"
            c.execute(query, (new_value, user_id,))
        conn.commit()
    except Exception as e:
        error(f"Error changing settings for user {user_id}: {e}")
        conn.rollback()


