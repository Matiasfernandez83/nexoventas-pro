"""
init_db.py — NexoVentas Pro V2
Crea el esquema y carga productos de ejemplo.
Ejecutar: python init_db.py
"""
import sqlite3

DATABASE = 'database.db'

SEED = [
    {
        "titulo": "Samsung Galaxy S24 Ultra 5G",
        "descripcion": "Titán de la fotografía. S-Pen integrado, cámara 200MP y pantalla Dynamic AMOLED 2X. Envío Full garantizado.",
        "precio": 1999999,
        "imagen_url": "https://images.unsplash.com/photo-1678911820864-e2c567c655d7?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA21444143",
        "categoria": "Smartphones",
        "estrellas": 5,
    },
    {
        "titulo": "iPhone 15 Pro Max 256 GB",
        "descripcion": "Titanio, cámara triple con zoom óptico 5x y el chip A17 Pro más rápido del mundo. En stock ahora.",
        "precio": 2450000,
        "imagen_url": "https://images.unsplash.com/photo-1696446701796-da61225697cc?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA27341852",
        "categoria": "Smartphones",
        "estrellas": 5,
    },
    {
        "titulo": "Sony WH-1000XM5 Noise Cancelling",
        "descripcion": "Cancelación de ruido líder en la industria. Autonomía de 30 horas. El favorito de viajeros y músicos.",
        "precio": 520000,
        "imagen_url": "https://images.unsplash.com/photo-1546435770-a3e426da4717?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA15949444",
        "categoria": "Audio",
        "estrellas": 5,
    },
    {
        "titulo": "Samsung Galaxy Tab S9 FE",
        "descripcion": "Pantalla 10.9″ TFT, procesador Exynos potente y resistencia IP68. Perfecta para estudio y entretenimiento.",
        "precio": 420000,
        "imagen_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA28135402",
        "categoria": "Tablets",
        "estrellas": 4,
    },
    {
        "titulo": "Smart TV LG 55\" OLED evo",
        "descripcion": "Negros perfectos, colores infinitos. Procesador α9 Gen6 con IA y Dolby Vision IQ. La TV del futuro, hoy.",
        "precio": 1850000,
        "imagen_url": "https://images.unsplash.com/photo-1593359677759-5437334eb91b?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA22262261",
        "categoria": "TV & Video",
        "estrellas": 5,
    },
    {
        "titulo": "Notebook Lenovo IdeaPad Slim 5",
        "descripcion": "Intel Core i5 13th Gen, 16 GB RAM, SSD 512 GB. Delgada, veloz y lista para el trabajo profesional.",
        "precio": 780000,
        "imagen_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA22262265",
        "categoria": "Computación",
        "estrellas": 4,
    },
    {
        "titulo": "Freidora de Aire Philips Airfryer XXL",
        "descripcion": "7.3 litros de capacidad, tecnología TurboStar. Cocina para toda la familia con hasta 90% menos grasa.",
        "precio": 195000,
        "imagen_url": "https://images.unsplash.com/photo-1585504706975-5137d7f6fe95?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA15116744",
        "categoria": "Hogar",
        "estrellas": 5,
    },
    {
        "titulo": "Aspiradora Robot Roomba j7+",
        "descripcion": "Detecta y esquiva obstáculos en tiempo real. Se vacía sola. Control total por app y compatible con Alexa.",
        "precio": 680000,
        "imagen_url": "https://images.unsplash.com/photo-1589652717521-10c0d092dea9?q=80&w=800&auto=format&fit=crop",
        "link_afiliado": "https://www.mercadolibre.com.ar/p/MLA16223444",
        "categoria": "Hogar",
        "estrellas": 5,
    },
]


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

    for p in SEED:
        c.execute(
            'INSERT INTO productos (titulo, descripcion, precio, imagen_url, link_afiliado, categoria, estrellas) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (p['titulo'], p['descripcion'], p['precio'],
             p['imagen_url'], p['link_afiliado'], p['categoria'], p['estrellas'])
        )

    conn.commit()
    conn.close()
    print(f"OK: Base de datos creada con {len(SEED)} productos de ejemplo.")


if __name__ == '__main__':
    init_db()
