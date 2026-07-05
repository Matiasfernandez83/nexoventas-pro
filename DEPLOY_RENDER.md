# Guía de despliegue en Render — NexoVentas Pro

Pasos para dejar una tienda instalada para un cliente, con datos e imágenes persistentes.

## 1. Base de datos Postgres (gratis)

1. En Render: **New → PostgreSQL** → plan Free → crear.
2. Copiar la **Internal Database URL** (empieza con `postgres://`).

> Sin `DATABASE_URL` la app usa SQLite local, que en Render **se borra en cada deploy**. Para producción siempre configurar Postgres.

## 2. Cloudinary para imágenes (gratis)

1. Crear cuenta en [cloudinary.com](https://cloudinary.com) (plan gratis: 25 GB).
2. En el Dashboard copiar la variable **CLOUDINARY_URL** (`cloudinary://KEY:SECRET@cloud_name`).

> Sin `CLOUDINARY_URL` las imágenes se guardan en `static/uploads`, que en Render también se borra en cada deploy.

## 3. Web Service

1. Subir el proyecto a un repo de GitHub.
2. En Render: **New → Web Service** → conectar el repo.
3. Runtime Python. Build: `pip install -r requirements.txt`. Start: `gunicorn app:app` (lo toma del Procfile).
4. En **Environment** agregar:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | una clave aleatoria larga (Render puede generarla) |
| `ADMIN_USER` | usuario del panel (ej. el nombre del cliente) |
| `ADMIN_PASSWORD` | contraseña fuerte, distinta por cliente |
| `DATABASE_URL` | la Internal Database URL del paso 1 |
| `CLOUDINARY_URL` | la URL del paso 2 |

5. Deploy. Verificar:
   - `/` carga la tienda vacía.
   - `/admin` redirige al login; entrar con las credenciales.
   - Cargar un producto con imagen → la URL de la imagen debe ser `https://res.cloudinary.com/...`.
   - Hacer un **Manual Deploy** de nuevo y confirmar que el producto sigue ahí (persistencia OK).

## 4. Dominio propio (opcional)

En el Web Service → **Settings → Custom Domains** → agregar el dominio del cliente y configurar el CNAME en el registrador.

## Desarrollo local

Sin variables de entorno la app corre igual: SQLite (`database.db`) + imágenes en `static/uploads` + admin `admin` / `admin123`.

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## Checklist por cada cliente nuevo

- [ ] Postgres nuevo (o schema separado) — **una base por cliente**
- [ ] `ADMIN_PASSWORD` única
- [ ] Carpeta Cloudinary distinta o cuenta del cliente
- [ ] Logo/nombre personalizado en `templates/base.html`
- [ ] Probar persistencia tras redeploy
