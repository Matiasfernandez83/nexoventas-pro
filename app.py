from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'nexoventas_v2_secret_2026'
DATABASE = 'database.db'

# ── Configuración de uploads ──────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Helpers de DB ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows):
    """Convierte sqlite3.Row → list[dict] con precio siempre float."""
    result = []
    for r in rows:
        d = dict(r)
        try:
            d['precio'] = float(str(d.get('precio', 0) or 0).replace(',', '.'))
        except (ValueError, TypeError):
            d['precio'] = 0.0
        result.append(d)
    return result

def ensure_db():
    """Crea la DB y la puebla con datos de ejemplo si está vacía."""
    conn = get_db()
    # Crear tabla si no existe
    conn.execute('''
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
    conn.commit()
    # Si la tabla está vacía, no insertar productos de ejemplo (eliminado a petición)
    conn.close()

# Auto-inicializar al arrancar
with app.app_context():
    ensure_db()


# ── Filtro de precio ──────────────────────────────────────────────────────────
@app.template_filter('precio_fmt')
def precio_fmt(valor):
    try:
        return f"${float(valor):,.0f}".replace(",", ".")
    except Exception:
        return str(valor)

# ── Rutas públicas ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    productos = rows_to_dicts(
        conn.execute('SELECT * FROM productos ORDER BY id DESC').fetchall()
    )
    categorias = [r['categoria'] for r in
                  conn.execute('SELECT DISTINCT categoria FROM productos').fetchall()]
    conn.close()
    return render_template('index.html', productos=productos, categorias=categorias)

# ── Admin ─────────────────────────────────────────────────────────────────────
@app.route('/admin')
def admin():
    conn = get_db()
    productos = rows_to_dicts(
        conn.execute('SELECT * FROM productos ORDER BY id DESC').fetchall()
    )
    conn.close()
    return render_template('admin.html', productos=productos)

@app.route('/admin/add', methods=['POST'])
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
        fname = f"{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        imagen_url = f"/static/uploads/{fname}"

    if not imagen_url:
        imagen_url = 'https://placehold.co/400x400/111/3D8BFF?text=Producto'

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO productos (titulo, descripcion, precio, imagen_url, link_afiliado, categoria, estrellas) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (titulo, descripcion, precio, imagen_url, link, categoria, estrellas)
        )
        conn.commit()
        flash(f'✓ "{titulo}" agregado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al guardar: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:pid>', methods=['POST'])
def admin_delete(pid):
    conn = get_db()
    try:
        p = conn.execute('SELECT titulo FROM productos WHERE id = ?', (pid,)).fetchone()
        conn.execute('DELETE FROM productos WHERE id = ?', (pid,))
        conn.commit()
        nombre = p['titulo'] if p else f'#{pid}'
        flash(f'"{nombre}" fue eliminado.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/update/<int:pid>', methods=['POST'])
def admin_update(pid):
    link   = (request.form.get('link_afiliado') or '').strip()
    precio_raw = (request.form.get('precio') or '0').strip()
    imagen_url = (request.form.get('imagen_url') or '').strip()
    try:
        precio = float(precio_raw.replace('.', '').replace(',', '.'))
    except ValueError:
        precio = 0.0
    conn = get_db()
    try:
        conn.execute(
            'UPDATE productos SET link_afiliado=?, precio=?, imagen_url=? WHERE id=?',
            (link, precio, imagen_url, pid)
        )
        conn.commit()
        flash(f'Producto #{pid} actualizado.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
