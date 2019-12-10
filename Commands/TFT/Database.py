import sqlite3 as sq3
import json
from typing import List, Dict, Any

class User:
    def __init__(self, discord_id, gold, champions_json):
        self.discord_id = discord_id
        self.gold = gold
        self.champions_json = json.dumps(champions_json)

def add_user_if_not_exist(default_value):
    def deco_wrap(function):
        def wrapper(self, discord_id):
            data = self.cursor.execute("SELECT discord_id FROM Users WHERE discord_id = ?",
                                       (discord_id,))
            user = data.fetchone()
            if not user:
                self.add_user(discord_id)
                if default_value is not None:
                    return default_value
            return function(self, discord_id)
        return wrapper
    return deco_wrap


class Database:
    conn = sq3.connect('data/tft.db')

    @classmethod
    def init_db(cls):
        cls.conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS Users (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             discord_id INTEGER NOT NULL,
             gold INTEGER NOT NULL,
             champions TEXT NOT NULL)
         """)

    def __init__(self):
        self.cursor = self.conn.cursor()  # type: sq3.Cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.conn.commit()
        self.cursor.close()

    def add_user(self, discord_id : int) -> None:
        self.cursor.execute("INSERT INTO Users(discord_id, gold, champions) VALUES (?, ?, ?)", (discord_id, 0, "[]"))

    def update_champions(self, discord_id : int, champs_json : List[Dict[str, Any]]) -> None:
        self.cursor.execute("UPDATE Users SET champions = ? WHERE discord_id = ?", (json.dumps(champs_json), discord_id))

    def update_gold(self, discord_id : int, gold : int) -> None:
        self.cursor.execute("UPDATE Users SET gold = ? WHERE discord_id = ?", (gold, discord_id))

    @add_user_if_not_exist([])
    def get_champions(self, discord_id : int) -> list:
        data = self.cursor.execute("SELECT champions FROM Users WHERE discord_id = ?", (discord_id,))
        json_str = data.fetchone()[0]
        return sorted(json.loads(json_str), key=lambda x: (-x['level'], x['name']))

    @add_user_if_not_exist(0)
    def get_gold(self, discord_id : int) -> int:
        data = self.cursor.execute("SELECT gold FROM Users WHERE discord_id = ?", (discord_id,))
        return data.fetchone()[0]

    @add_user_if_not_exist(None)
    def get_user(self, discord_id : int) -> User:
        data = self.cursor.execute("SELECT discord_id, gold, champions FROM Users WHERE discord_id = ?", (discord_id,))
        user = data.fetchone()
        return User(*user)


Database.init_db()