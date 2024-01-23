import os.path
import sqlite3

if os.path.exists('..\\global_clock_db.sqlite3'):
    print('WARNING: A database file was already found!\nRunning the program will reset the database.')
    res = input('Are you sure you want to keep going? [Y/N]: ')

    while res.lower() not in ["y", "n", "yes", "no"]:
        print('Invalid input.')
        res = input('Are you sure you want to keep going? [Y/N]: ')

    if res.lower() not in ["y", "yes"]:
        print('Exiting...')
        exit()

    print('Removing old database')
    os.remove('..\\global_clock_db.sqlite3')

print('Generating database')

connection = sqlite3.connect(
    database='..\\global_clock_db.sqlite3'
)

try:
    crsr = connection.cursor()
    crsr.execute(
        "CREATE TABLE IF NOT EXISTS user_data ("
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
