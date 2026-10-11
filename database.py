
"""Create and use a small SQLite database with fictional banking data."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(
    os.getenv("BANK_DB_PATH", Path(__file__).with_name("banking_demo.db"))
)


@contextmanager
def connect():
    """Open and close the database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def query_one(sql, values=()):
    with connect() as connection:
        row = connection.execute(sql, values).fetchone()
        return dict(row) if row else None


def query_all(sql, values=()):
    with connect() as connection:
        rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]


def setup_database(reset=False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()

    with connect() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                income REAL NOT NULL,
                existing_emi REAL NOT NULL,
                credit_score INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                customer_id TEXT PRIMARY KEY,
                balance REAL NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                merchant TEXT NOT NULL,
                amount REAL NOT NULL,
                kind TEXT NOT NULL,
                international INTEGER DEFAULT 0,
                new_device INTEGER DEFAULT 0,
                late_night INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
        """)

        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        if count:
            return

        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            [
                ("C101", "Asha Kumar", 90000, 12000, 760),
                ("C102", "Ravi Shah", 45000, 19000, 620),
                ("C103", "Maya Iyer", 125000, 18000, 720),
            ],
        )

        connection.executemany(
            "INSERT INTO accounts VALUES (?, ?)",
            [
                ("C101", 85000),
                ("C102", 32000),
                ("C103", 180000),
            ],
        )

        now = datetime.now(timezone.utc)

        samples = [
            ("C101", "Groceries", 2200, "debit", 0, 0, 0, 1),
            ("C101", "Book Store", 950, "debit", 0, 0, 0, 2),
            ("C101", "Salary", 90000, "credit", 0, 0, 0, 3),
            ("C102", "Online Store", 18000, "debit", 0, 1, 0, 1),
            ("C102", "Cafe", 350, "debit", 0, 0, 0, 3),
            ("C103", "Fuel", 3100, "debit", 0, 0, 0, 1),
            ("C103", "Travel", 56000, "debit", 1, 1, 1, 2),
        ]

        for customer_id, merchant, amount, kind, abroad, device, night, days in samples:
            created_at = (now - timedelta(days=days)).isoformat()

            connection.execute(
                """
                INSERT INTO transactions
                (customer_id, merchant, amount, kind, international,
                 new_device, late_night, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    merchant,
                    amount,
                    kind,
                    abroad,
                    device,
                    night,
                    created_at,
                ),
            )


def add_demo_transaction(
    customer_id, amount, merchant, international, new_device, late_night
):
    """Save a debit in the fictional banking database."""

    created_at = datetime.now(timezone.utc).isoformat()

    with connect() as connection:
        updated = connection.execute(
            """
            UPDATE accounts
            SET balance = balance - ?
            WHERE customer_id = ? AND balance >= ?
            """,
            (amount, customer_id, amount),
        )

        if updated.rowcount != 1:
            return None

        cursor = connection.execute(
            """
            INSERT INTO transactions
            (customer_id, merchant, amount, kind, international,
             new_device, late_night, created_at)
            VALUES (?, ?, ?, 'debit', ?, ?, ?, ?)
            """,
            (
                customer_id,
                merchant,
                amount,
                int(international),
                int(new_device),
                int(late_night),
                created_at,
            ),
        )

        return cursor.lastrowid
