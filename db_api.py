import sqlite3

class ContextCursorFactory:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def __enter__(self):
        self.active_cursor = self.connection.cursor()
        return self.active_cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active_cursor.close()


class DB_API:
    def __init__(self):
        self.connection = sqlite3.connect('global_clock_db.sqlite3')

    def cursor(self):
        return ContextCursorFactory(self.connection)

    def add_user(self, discord_id: int, timezone: str) -> bool:
        success = True
        with self.cursor() as crsr:
            try:
                crsr.execute("REPLACE INTO user_data VALUES (?, ?)", (discord_id, timezone))
            except sqlite3.Error:
                success = False
        self.connection.commit()
        return success

    def remove_user(self, discord_id: int):
        success = True
        with self.cursor() as crsr:
            try:
                crsr.execute("DELETE FROM user_data WHERE discord_id = ?", (discord_id,))
            except sqlite3.Error:
                success = False
        return success

    def get_user(self, discord_id: int) -> tuple:
        with self.cursor() as crsr:
            res = crsr.execute("SELECT FROM user_data WHERE discord_id = ?", (discord_id, ))
        return res.fetchone()

    def get_user_timezone(self, discord_id: int) -> str:
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


