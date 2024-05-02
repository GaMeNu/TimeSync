import os

from dotenv import load_dotenv
from mysql import connector as database
'''
class ContextCursorFactory:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def __enter__(self):
        self.active_cursor = self.connection.cursor()
        return self.active_cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active_cursor.close()
'''

load_dotenv()
DATABASE = os.getenv("DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("PASSWORD")

class DB_API:
    def __init__(self):
        self.connection = database.connect(
            host="localhost",
            port=8080,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DATABASE
        )
        print(self.connection.is_connected())

    def cursor(self):
        return self.connection.cursor()

    def add_user(self, discord_id: int, timezone: str) -> bool:
        success = True
        with self.cursor() as crsr:
            try:
                crsr.execute("REPLACE INTO user_data VALUES (?, ?)", (discord_id, timezone))
            except db.Error:
                success = False
        self.connection.commit()
        return success

    def remove_user(self, discord_id: int):
        success = True
        with self.cursor() as crsr:
            try:
                crsr.execute("DELETE FROM user_data WHERE discord_id = ?", (discord_id,))
            except db.Error:
                success = False
        return success

    def get_user(self, discord_id: int) -> tuple:
        with self.cursor() as crsr:
            res = crsr.execute("SELECT FROM user_data WHERE discord_id = ?", (discord_id, ))
        return res.fetchone()

    def get_user_timezone(self, discord_id: int) -> str | None:
        with self.cursor() as crsr:
            crsr.execute("SELECT timezone FROM user_data WHERE discord_id = ?", (discord_id,))
            res = crsr.fetchone()

        if res is None:
            return None
        return res[0]




if __name__ == '__main__':
    db = DB_API()
    db.add_user(1, "Asia/Jerusalem")
    db.add_user(2, "Asia/Jerusalem")
    with db.cursor() as crsr:
        crsr.execute("SELECT * FROM user_data")
        print(crsr.fetchall())
    print(db.get_user_timezone(1))
    db.remove_user(1)
    with db.cursor() as crsr:
        crsr.execute("SELECT * FROM user_data")
        print(crsr.fetchall())
    db.remove_user(2)


