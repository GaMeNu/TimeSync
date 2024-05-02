import os.path
from db import __filename__
from mysql import connector as db
def create_db():
    if os.path.exists(__filename__):
        print('WARNING: A database file was already found!\nRunning the program will reset the database.')
        res = input('Are you sure you want to keep going? [Y/N]: ')

        while res.lower() not in ["y", "n", "yes", "no"]:
            print('Invalid input.')
            res = input('Are you sure you want to keep going? [Y/N]: ')

        if res.lower() not in ["y", "yes"]:
            print('Exiting...')
            exit()

        print('Removing old database')
        os.remove(__filename__)

    print('Generating database')

    connection = db.connect(
        database=__filename__
    )

    try:
        crsr = connection.cursor()
        crsr.execute(
            "CREATE TABLE IF NOT EXISTS timezones ("
            "discord_id INTEGER PRIMARY KEY NOT NULL,"
            "timezone TEXT NOT NULL"
            ");")
        crsr.close()
        connection.commit()
    except Exception as e:
        print(f'Failed to generate db. Details:\n{e}\n\nAborting...')
        connection.rollback()

    connection.close()

    print('Done!')

if __name__ == '__main__':
    create_db()
