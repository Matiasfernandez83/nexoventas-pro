"""
init_db.py — NexoVentas Pro V2
Crea el esquema y carga productos de ejemplo.
Ejecutar: python init_db.py
"""
import sqlite3

DATABASE = 'database.db'

SEED = []


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.executescript('''
        DROP TABLE IF EXISTS productos;

        CREATE TABLE productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo        TEXT    NOT NULL,
            descripcion   TEXT    DEFAULT '',
            precio        REAL    DEFAULT 0,
            imagen_url    TEXT    DEFAULT '',
            link_afiliado TEXT    NOT NULL,
            categoria     TEXT    DEFAULT 'General',
            estrellas     INTEGER DEFAULT 5
        );
    ''')

    conn.commit()
    conn.close()
    print("OK: Base de datos creada (vacía, sin productos de ejemplo).")


if __name__ == '__main__':
    init_db()
