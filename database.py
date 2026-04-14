import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_NAME = "scadenziario.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        description TEXT,
        due_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        plate TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        content TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        description TEXT,
        cost REAL,
        workshop TEXT,
        date TEXT
    )
    """)


    conn.commit()
    conn.close()

def add_deadline(vehicle_id, description, due_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO deadlines (vehicle_id, description, due_date)
    VALUES (?, ?, ?)
    """, (vehicle_id, description, due_date))

    conn.commit()
    conn.close()


def get_deadlines_by_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM deadlines WHERE vehicle_id = ?
    ORDER BY due_date ASC
    """, (vehicle_id,))

    deadlines = cursor.fetchall()
    conn.close()
    return deadlines

def create_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    hashed = generate_password_hash(password)

    cursor.execute("""
    INSERT INTO users (name, email, password)
    VALUES (?, ?, ?)
    """, (name, email, hashed))

    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()
    return user

def add_vehicle(user_id, name, plate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO vehicles (user_id, name, plate)
    VALUES (?, ?, ?)
    """, (user_id, name, plate))

    conn.commit()
    conn.close()


def get_vehicles_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM vehicles WHERE user_id = ?
    """, (user_id,))

    vehicles = cursor.fetchall()
    conn.close()
    return vehicles

def get_vehicle_by_id(vehicle_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM vehicles
    WHERE id = ? AND user_id = ?
    """, (vehicle_id, user_id))

    vehicle = cursor.fetchone()
    conn.close()
    return vehicle

def get_all_deadlines_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT deadlines.*, vehicles.name as vehicle_name
    FROM deadlines
    JOIN vehicles ON deadlines.vehicle_id = vehicles.id
    WHERE vehicles.user_id = ?
    ORDER BY due_date ASC
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()
    return data

def add_note(vehicle_id, content):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
    INSERT INTO notes (vehicle_id, content, created_at)
    VALUES (?, ?, ?)
    """, (vehicle_id, content, created_at))

    conn.commit()
    conn.close()


def get_notes_by_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM notes
    WHERE vehicle_id = ?
    ORDER BY id DESC
    """, (vehicle_id,))

    notes = cursor.fetchall()
    conn.close()
    return notes

def delete_note(note_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM notes WHERE id = ?
    """, (note_id,))

    conn.commit()
    conn.close()


def delete_deadline(deadline_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM deadlines WHERE id = ?
    """, (deadline_id,))

    conn.commit()
    conn.close()


def add_maintenance(vehicle_id, description, cost, workshop, date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO maintenances (vehicle_id, description, cost, workshop, date)
    VALUES (?, ?, ?, ?, ?)
    """, (vehicle_id, description, cost, workshop, date))

    conn.commit()
    conn.close()


def get_maintenances_by_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM maintenances
    WHERE vehicle_id = ?
    ORDER BY date DESC
    """, (vehicle_id,))

    data = cursor.fetchall()
    conn.close()
    return data

def delete_maintenance(maintenance_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM maintenances WHERE id = ?
    """, (maintenance_id,))

    conn.commit()
    conn.close()

def delete_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    # elimina dati collegati
    cursor.execute("DELETE FROM deadlines WHERE vehicle_id = ?", (vehicle_id,))
    cursor.execute("DELETE FROM maintenances WHERE vehicle_id = ?", (vehicle_id,))
    cursor.execute("DELETE FROM notes WHERE vehicle_id = ?", (vehicle_id,))

    # elimina veicolo
    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))

    conn.commit()
    conn.close()

def get_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    vehicle = cursor.fetchone()

    conn.close()
    return vehicle

def get_deadlines(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM deadlines WHERE vehicle_id = ?", (vehicle_id,))
    data = cursor.fetchall()

    conn.close()
    return data

def get_maintenances(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM maintenances WHERE vehicle_id = ?", (vehicle_id,))
    data = cursor.fetchall()

    conn.close()
    return data

def get_notes(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE vehicle_id = ?", (vehicle_id,))
    data = cursor.fetchall()

    conn.close()
    return data

