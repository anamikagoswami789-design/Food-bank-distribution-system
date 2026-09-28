"""
database.py
============
Responsible for everything related to the SQLite database:
    - Opening a connection
    - Creating tables (only if they do not already exist)
    - Nothing else lives here on purpose, so it is easy to find
      and easy to understand.

This file does NOT contain any business rules (like "priority must
be Critical/Emergency/Normal") and it does NOT contain any GUI code.
Those live in backend.py and gui.py.
"""

import sqlite3

DB_NAME = "food_bank.db"


def get_connection():
    """
    Opens (or creates) the SQLite database file and returns a
    connection object. SQLite automatically creates the .db file
    the first time this runs if it does not already exist.
    """
    conn = sqlite3.connect(DB_NAME)
    # Keeps foreign key constraints active (off by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """
    Creates all required tables if they do not already exist.
    This is safe to run every time the app starts - it will NOT
    delete or overwrite any existing data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            donor_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary TEXT NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            priority INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary TEXT NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            distribution_date TEXT NOT NULL,
            request_id INTEGER,
            FOREIGN KEY (request_id) REFERENCES requests (id)
        )
    """)

    conn.commit()
    conn.close()
