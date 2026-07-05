# Landing NexoVentas Pro — lista para publicar

Carpeta lista para deploy como sitio estático. Un solo archivo: `index.html`.

## Antes de publicar (2 minutos)

1. **Tu número de WhatsApp** — abrir `index.html`, buscar el bloque `CONFIG` (está al inicio del `<script>`) y cambiar:
   ```js
   WHATSAPP: "5491100000000",   // ← tu número real, sin "+" (ej: 5491133334444)
   DEMO_URL: "https://nexoventas-pro.onrender.com/"  // ← URL real de tu demo en Render
   ```
   Ese número se usa en el botón flotante verde y en el formulario de compra.

2. **Screenshot del panel** (opcional pero recomendado) — sacale una captura al panel admin de NexoVentas y guardala como `manual.jpg` en esta carpeta. Si no existe, se muestra un placeholder.

## Publicar gratis

**Opción A — Netlify Drop (la más rápida):**
1. Entrar a https://app.netlify.com/drop
2. Arrastrar esta carpeta completa. Listo, te da una URL pública al instante.

**Opción B — Render (todo en un solo lugar):**
1. Subir esta carpeta a un repo de GitHub.
2. En Render: **New → Static Site** → conectar el repo → Publish directory: `.`

**Dominio propio:** en Netlify/Render → Custom Domains → agregar tu dominio y configurar el CNAME en el registrador.

## Qué incluye

- Multi-idioma (ES / EN / PT)
- Planes: suscripción mensual $20.000 ARS y código propio $200.000 ARS
- Formulario de compra que deriva a tu WhatsApp con los datos del cliente
- Botón flotante de WhatsApp para consultas
- Testimonios, beneficios y sección "cómo funciona"
- Meta tags para verse bien al compartir en redes

## Probar en local

```bash
python -m http.server 8765 --directory .
# http://localhost:8765
```
