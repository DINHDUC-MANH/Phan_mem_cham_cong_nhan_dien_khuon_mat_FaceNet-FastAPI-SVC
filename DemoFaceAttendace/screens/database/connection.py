import sqlite3

DB_PATH = "database.db"

def connect():
    return sqlite3.connect(DB_PATH)