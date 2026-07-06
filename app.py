from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
import sqlite3
import os
import time
import hmac
import json
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ── Configuración por variables de entorno ────────────────────────────────────
# En Render definir: SECRET_KEY, ADMIN_PASSWORD, DATABASE_URL, CLOUDINARY_URL
app.secret_key = os.environ.get('SECRET_KEY', 'dev-solo-local-cambiar-en-produccion')

ADMIN_USER     = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

DATABASE     = os.environ.get('DB_PATH', 'database.db')  # SQLite local
DATABASE_URL = os.environ.get('DATABASE_URL', '')        # Postgres en Render
USE_POSTGRES = DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
USE_CLOUDINARY = bool(CLOUDINARY_URL)

if USE_CLOUDINARY:
    import cloudinary
    import cloudinary.uploader

# ── Configuración de uploads (solo modo local, sin Cloudinary) ────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Helpers de DB (SQLite local / Postgres en producción) ─────────────────────
def get_db():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def adapt(sql):
    """Los queries usan placeholders '?'; Postgres necesita '%s'."""
    return sql.replace('?', '%s') if USE_POSTGRES else sql

def db_query(sql, params=(), fetch=None):
    """Ejecuta un query y devuelve filas como dicts. fetch: 'all' | 'one' | None."""
    conn = get_db()
    try:
        if USE_POSTGRES:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = conn.cursor()
        cur.execute(adapt(sql), params)
        result = None
        if fetch == 'all':
            result = [dict(r) for r in cur.fetchall()]
        elif fetch == 'one':
            row = cur.fetchone()
            result = dict(row) if row else None
        conn.commit()
        return result
    finally:
        conn.close()

def normalizar_precio(productos):
    """Asegura que precio sea siempre float."""
    for d in productos:
        try:
            d['precio'] = float(str(d.get('precio', 0) or 0).replace(',', '.'))
        except (ValueError, TypeError):
            d['precio'] = 0.0
    return productos

def ensure_db():
    """Crea la tabla de productos si no existe."""
    if USE_POSTGRES:
        db_query('''
            CREATE TABLE IF NOT EXISTS productos (
                id            SERIAL PRIMARY KEY,
                titulo        TEXT NOT NULL,
                descripcion   TEXT DEFAULT '',
                precio        REAL DEFAULT 0,
                imagen_url    TEXT DEFAULT '',
                link_afiliado TEXT NOT NULL,
                categoria     TEXT DEFAULT 'General',
                estrellas     INTEGER DEFAULT 5
            )
        ''')
    else:
        db_query('''
            CREATE TABLE IF NOT EXISTS productos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo        TEXT    NOT NULL,
                descripcion   TEXT    DEFAULT '',
                precio        REAL    DEFAULT 0,
                imagen_url    TEXT    DEFAULT '',
                link_afiliado TEXT    NOT NULL,
                categoria     TEXT    DEFAULT 'General',
                estrellas     INTEGER DEFAULT 5
            )
        ''')

# ── Seed de productos demo (solo si SEED_DEMO=1 y la tabla está vacía) ────────
SEED_PRODUCTOS = [
    ("Auriculares Inalámbricos Xiaomi Redmi Buds 6 Play BT 5.4",
     "El auricular más vendido de Argentina. Bluetooth 5.4, hasta 36hs de batería con el estuche y cancelación de ruido en llamadas. Ideal para música, gym y trabajo.",
     24999, "https://http2.mlstatic.com/D_NQ_NP_2X_935289-MLA100007937509_122025-F.webp",
     "https://www.mercadolibre.com.ar/audifonos-inalambricos-xiaomi-redmi-buds-6-play-bt-54-color-sky-blue/p/MLA55462947",
     "Audio", 5,
      ["https://http2.mlstatic.com/D_NQ_NP_2X_782183-MLA95705710992_102025-F.webp", "https://http2.mlstatic.com/D_NQ_NP_2X_693078-MLA98841781353_112025-F.webp", "https://http2.mlstatic.com/D_NQ_NP_2X_677877-MLA98876241593_112025-F.webp"]),
    ("Celular Samsung Galaxy A16 128GB 4GB RAM 6.7\"",
     "El celular más elegido del país. Pantalla Super AMOLED de 6.7\", cámara de 50MP y batería para todo el día. Envío gratis y garantía oficial Samsung.",
     309999, "https://http2.mlstatic.com/D_NQ_NP_2X_909065-MLA96870019085_102025-F.webp",
     "https://www.mercadolibre.com.ar/celular-samsung-galaxy-a16-128-gb-4-gb-de-ram-67-gris/p/MLA44113908",
     "Smartphones", 5,
      ["https://http2.mlstatic.com/D_NQ_NP_2X_911302-MLA99950138601_112025-F.webp"]),
    ("Auriculares Bluetooth Sony WH-CH520 On-Ear",
     "Calidad de sonido Sony con 50 horas de batería y carga rápida. Vincha liviana y cómoda para usar todo el día. Conexión multipunto: celular y compu a la vez.",
     84999, "https://http2.mlstatic.com/D_NQ_NP_2X_941567-MLA99464084588_112025-F.webp",
     "https://www.mercadolibre.com.ar/auriculares-bluetooth-inalambricos-sony-wh-ch520-amarillo/p/MLA47857275",
     "Audio", 5,
      ["https://http2.mlstatic.com/D_NQ_NP_2X_829441-MLA99993059381_112025-F.webp"]),
    ("Smartwatch Redmi Watch 5 Active con Alexa",
     "Reloj inteligente con pantalla LCD de 2\", Alexa integrada, más de 140 modos deportivos y hasta 18 días de batería. Recibí llamadas y notificaciones en tu muñeca.",
     71986, "https://http2.mlstatic.com/D_NQ_NP_2X_954866-MLA99462258698_112025-F.webp",
     "https://www.mercadolibre.com.ar/reloj-inteligente-redmi-watch-5-active-hyperos-alexa-silver/p/MLA47354382",
     "Accesorios", 4,
      []),
    ("Power Bank 20.000mAh Carga Rápida",
     "Batería portátil de 20.000mAh: carga tu celular 4 veces completas. Doble salida USB para cargar dos dispositivos a la vez. El accesorio que salva viajes y cortes de luz.",
     23000, "https://http2.mlstatic.com/D_NQ_NP_2X_991674-MLA98648255379_112025-F.webp",
     "https://articulo.mercadolibre.com.ar/MLA-1399965089-power-bank-cargador-portatil-20000mah-carga-rapida-mixio-_JM",
     "Accesorios", 4,
      []),
    ("Samsung Galaxy Fit 3 Banda Deportiva AMOLED 1.6\"",
     "Pantalla AMOLED de 1.6\", 13 días de batería, más de 100 modos de ejercicio y monitoreo de sueño. La banda deportiva de Samsung a mitad de precio.",
     69999, "https://http2.mlstatic.com/D_NQ_NP_2X_702327-MLA99937462709_112025-F.webp",
     "https://www.mercadolibre.com.ar/samsung-galaxy-fit-3-sport-rosa-pantalla-tactil-amoled-16-bluetooth-microfono-13-dias-de-bateria/p/MLA33997619",
     "Accesorios", 5,
      ["https://http2.mlstatic.com/D_NQ_NP_2X_617547-MLA76395100597_052024-F.webp", "https://http2.mlstatic.com/D_NQ_NP_2X_624676-MLA75207394706_032024-F.webp", "https://http2.mlstatic.com/D_NQ_NP_2X_643676-MLA75438237975_032024-F.webp"]),
    ("Secador de Pelo Daewoo 2100W Frío/Calor con Difusor",
     "El electrodoméstico más vendido de ML. 2100W de potencia profesional, aire frío y caliente, y difusor incluido para rulos. 55% de descuento.",
     35599, "https://http2.mlstatic.com/D_NQ_NP_2X_872804-MLA99453742720_112025-F.webp",
     "https://www.mercadolibre.com.ar/secador-pelo-daewoo-2100w-frio-calor-con-difusor-dhd7007-negro/p/MLA22138728",
     "Hogar", 5,
      []),
    ("Aspiradora Gadnic 2 en 1 Vertical y de Mano 600W HEPA",
     "Aspiradora vertical que se convierte en aspiradora de mano. Filtro HEPA lavable, 15Kpa de succión y cable de 5 metros. Limpieza completa sin bolsas.",
     73999, "https://http2.mlstatic.com/D_NQ_NP_2X_928530-MLA109897100656_042026-F.webp",
     "https://www.mercadolibre.com.ar/aspiradora-gadnic-jtl60y-2-en-1-vertical-y-de-mano-600w-15kpa-filtro-hepa-lavable-cable-5m-deposito-1l/p/MLA45758897",
     "Hogar", 4,
      []),
    ("Cafetera Moulinex Dolce Gusto Piccolo XS",
     "La cafetera de cápsulas más buscada: café, capuccino y chocolatada en 30 segundos. Compacta, ideal para cocinas chicas. 49% OFF y envío gratis.",
     136990, "https://http2.mlstatic.com/D_NQ_NP_2X_994334-MLA100010184303_122025-F.webp",
     "https://www.mercadolibre.com.ar/cafetera-moulinex-dolce-gusto-piccolo-xs-pv1a0558/p/MLA15705813",
     "Cocina", 5,
      []),
    ("Proyector Portátil 4K HY300 Android 11 WiFi Bluetooth",
     "Cine en tu casa: proyecta hasta 130 pulgadas con Android 11 integrado (Netflix, YouTube sin nada extra). WiFi, Bluetooth y parlante incluido. El producto viral del año.",
     75122, "https://http2.mlstatic.com/D_NQ_NP_2X_907176-MLA96142511857_102025-F.webp",
     "https://www.mercadolibre.com.ar/proyector-portatil-4k-hy300-full-hd-wifi-hdmi-android-11-bt-50/p/MLA42238146",
     "TV & Video", 5,
      ["https://http2.mlstatic.com/D_NQ_NP_2X_706831-MLA80171884101_102024-F.webp", "https://http2.mlstatic.com/D_NQ_NP_2X_940421-MLA80171884099_102024-F.webp"]),
]

def seed_demo():
    """Carga productos demo una sola vez (controlado por env SEED_DEMO=1).
    Si los productos ya existen, solo completa las galerías de fotos vacías."""
    if os.environ.get('SEED_DEMO') != '1':
        return
    existentes = db_query('SELECT COUNT(*) AS c FROM productos', fetch='one')
    if existentes and existentes['c'] > 0:
        for titulo, _d, _p, _i, _l, _c, _e, extras in SEED_PRODUCTOS:
            if extras:
                db_query(
                    "UPDATE productos SET imagenes=? WHERE titulo=? AND (imagenes IS NULL OR imagenes='')",
                    (json.dumps(extras), titulo)
                )
        return
    for titulo, desc, precio, img, link, cat, estrellas, extras in SEED_PRODUCTOS:
        db_query(
            'INSERT INTO productos (titulo, descripcion, precio, imagen_url, link_afiliado, categoria, estrellas, imagenes) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (titulo, desc, precio, img, link, cat, estrellas, json.dumps(extras) if extras else '')
        )

def migrate_db():
    """Migraciones suaves: agrega columnas nuevas sin tocar datos existentes."""
    try:
        db_query("ALTER TABLE productos ADD COLUMN imagenes TEXT DEFAULT ''")
    except Exception:
        pass  # la columna ya existe

def parsear_imagenes(productos):
    """Agrega imagenes_list a cada producto: [imagen principal + extras]."""
    for d in productos:
        extras = []
        raw = d.get('imagenes') or ''
        if raw:
            try:
                extras = [u for u in json.loads(raw) if isinstance(u, str) and u.strip()]
            except (ValueError, TypeError):
                extras = [u.strip() for u in raw.splitlines() if u.strip()]
        principal = d.get('imagen_url') or ''
        d['imagenes_list'] = [principal] + [u for u in extras if u != principal] if principal else extras
    return productos

# Auto-inicializar al arrancar
with app.app_context():
    ensure_db()
    migrate_db()
    seed_demo()


# ── Autenticación del panel admin ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return wrapper

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged'):
        return redirect(url_for('admin'))
    if request.method == 'POST':
        user = (request.form.get('usuario') or '').strip()
        pwd  = request.form.get('password') or ''
        if hmac.compare_digest(user, ADMIN_USER) and hmac.compare_digest(pwd, ADMIN_PASSWORD):
            session['admin_logged'] = True
            session.permanent = False
            return redirect(request.args.get('next') or url_for('admin'))
        flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('index'))


# ── Filtro de precio ──────────────────────────────────────────────────────────
@app.template_filter('precio_fmt')
def precio_fmt(valor):
    try:
        return f"${float(valor):,.0f}".replace(",", ".")
    except Exception:
        return str(valor)

# ── Rutas públicas ────────────────────────────────────────────────────────────
@app.route('/ventas')
def ventas():
    """Landing de venta del producto. Servida solo si existe landing/index.html
    (para instalaciones de clientes basta borrar la carpeta landing/)."""
    landing_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'landing', 'index.html')
    if not os.path.exists(landing_path):
        return redirect(url_for('index'))
    with open(landing_path, encoding='utf-8') as f:
        return f.read()

@app.route('/')
def index():
    productos = parsear_imagenes(normalizar_precio(
        db_query('SELECT * FROM productos ORDER BY id DESC', fetch='all')
    ))
    categorias = sorted({p['categoria'] for p in productos})
    return render_template('index.html', productos=productos, categorias=categorias)

# ── Admin ─────────────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
def admin():
    productos = normalizar_precio(
        db_query('SELECT * FROM productos ORDER BY id DESC', fetch='all')
    )
    return render_template('admin.html', productos=productos)

@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add():
    titulo      = (request.form.get('titulo')      or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip()
    precio_raw  = (request.form.get('precio')      or '0').strip()
    link        = (request.form.get('link_afiliado') or '').strip()
    categoria   = (request.form.get('categoria')   or 'General').strip()
    estrellas   = int(request.form.get('estrellas', 5))

    # Validaciones básicas
    if not titulo:
        flash('El título es obligatorio.', 'error'); return redirect(url_for('admin'))
    if not link:
        flash('El link de afiliado es obligatorio.', 'error'); return redirect(url_for('admin'))

    try:
        precio = float(precio_raw.replace('.', '').replace(',', '.'))
    except ValueError:
        flash('El precio debe ser un número válido.', 'error'); return redirect(url_for('admin'))

    # Imagen: archivo > URL
    imagen_url = (request.form.get('imagen_url') or '').strip()
    file = request.files.get('imagen_file')
    if file and file.filename and allowed_file(file.filename):
        if USE_CLOUDINARY:
            try:
                res = cloudinary.uploader.upload(file, folder='nexoventas')
                imagen_url = res['secure_url']
            except Exception as e:
                flash(f'Error al subir la imagen: {e}', 'error')
                return redirect(url_for('admin'))
        else:
            fname = f"{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            imagen_url = f"/static/uploads/{fname}"

    if not imagen_url:
        imagen_url = 'https://placehold.co/400x400/111/3D8BFF?text=Producto'

    # Fotos adicionales (una URL por línea) para el carrusel de la tarjeta
    extras_raw = (request.form.get('imagenes_extra') or '').strip()
    extras = [u.strip() for u in extras_raw.splitlines() if u.strip().startswith('http')]
    imagenes_json = json.dumps(extras) if extras else ''

    try:
        db_query(
            'INSERT INTO productos (titulo, descripcion, precio, imagen_url, link_afiliado, categoria, estrellas, imagenes) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (titulo, descripcion, precio, imagen_url, link, categoria, estrellas, imagenes_json)
        )
        flash(f'✓ "{titulo}" agregado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al guardar: {e}', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:pid>', methods=['POST'])
@login_required
def admin_delete(pid):
    try:
        p = db_query('SELECT titulo FROM productos WHERE id = ?', (pid,), fetch='one')
        db_query('DELETE FROM productos WHERE id = ?', (pid,))
        nombre = p['titulo'] if p else f'#{pid}'
        flash(f'"{nombre}" fue eliminado.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/update/<int:pid>', methods=['POST'])
@login_required
def admin_update(pid):
    link   = (request.form.get('link_afiliado') or '').strip()
    precio_raw = (request.form.get('precio') or '0').strip()
    imagen_url = (request.form.get('imagen_url') or '').strip()
    try:
        precio = float(precio_raw.replace('.', '').replace(',', '.'))
    except ValueError:
        precio = 0.0
    try:
        db_query(
            'UPDATE productos SET link_afiliado=?, precio=?, imagen_url=? WHERE id=?',
            (link, precio, imagen_url, pid)
        )
        flash(f'Producto #{pid} actualizado.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
