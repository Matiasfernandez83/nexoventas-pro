from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
import sqlite3
import os
import time
import hmac
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

# Auto-inicializar al arrancar
with app.app_context():
    ensure_db()


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
    productos = normalizar_precio(
        db_query('SELECT * FROM productos ORDER BY id DESC', fetch='all')
    )
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

    try:
        db_query(
            'INSERT INTO productos (titulo, descripcion, precio, imagen_url, link_afiliado, categoria, estrellas) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (titulo, descripcion, precio, imagen_url, link, categoria, estrellas)
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
