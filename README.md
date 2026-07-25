# GestiónOne

**Plataforma SaaS de gestión comercial** desarrollada en Flask con arquitectura modular, multiempresa y diseño moderno inspirado en Stripe / Notion / Linear.

---

## ✨ Funcionalidades

- 🔐 **Autenticación** con 3 roles: `administrador`, `vendedor`, `consulta`
- 🏢 **Multiempresa** (cada usuario opera bajo el contexto de una empresa)
- 👥 **Clientes** — CRUD con búsqueda en vivo (HTMX)
- 📦 **Productos / Servicios** — CRUD y API JSON
- 📄 **Cotizaciones** — filas dinámicas, cálculo automático de IVA, aprobación, anulación y conversión a cuenta de cobro
- 🧾 **Cuentas de cobro** — pendiente / pagada / anulada con seguimiento
- 🎨 **Layout Designer (GrapesJS)** — diseñador visual de plantillas PDF arrastrables
- 📊 **Dashboard** con KPIs y gráficas Chart.js (ventas mensuales + estado de cartera)
- 📨 **Envío por correo** con PDF adjunto (SMTP)
- 📑 **Generación de PDF** con WeasyPrint (fallback a HTML si las libs nativas no están disponibles)
- 🛡 **Auditoría** completa de todas las acciones
- 🎨 **UI moderna** con Bootstrap 5, Inter font y CSS personalizado

---

## 🎨 Plantilla pre-cargada: "Cuenta de cobro — Estilo Verde"

El proyecto incluye una plantilla profesional lista para usar, con:

- Tamaño **A5** vertical (compacto, sin espacio desperdiciado)
- Tipografía **Century Gothic** (con fallback a Questrial — fuente libre estilo geométrico incluida en el proyecto)
- Encabezado verde + fecha resaltada
- Filas CLIENTE/NIT y DEBE A/C.C
- Tabla de concepto, cantidad, valor unitario y total
- Métodos de pago (LLAVE, DAVIPLATA, NEQUI) — **editables desde el formulario de empresa**, no hace falta abrir GrapesJS
- Tu firma personal (incrustada en base64, no requiere URL externa)
- Nota regulatoria del artículo 8383 ley 1819 de 2016
- Valor en letras auto-generado (TRESCIENTOS MIL PESOS) usando `num2words`

**Para cargarla en la base de datos** después de la primera ejecución:

```bash
python crear_plantilla_verde.py
```

Esto crea/actualiza la plantilla y la marca como predeterminada para cuentas de cobro.

La firma se encuentra en `app/static/img/firma.png`. Para cambiarla, reemplaza el archivo y vuelve a ejecutar el script.

### Configurar tus métodos de pago

Desde el menú **Empresas → editar tu empresa**, llena los campos:

| Campo                | Variable en plantilla | Ejemplo                       |
|----------------------|-----------------------|-------------------------------|
| Llave / Transfiya    | `{{pago_llave}}`      | `1074135696`                  |
| Daviplata            | `{{pago_daviplata}}`  | `3012979313`                  |
| Nequi                | `{{pago_nequi}}`      | `3012979313`                  |
| Etiqueta extra       | `{{pago_extra_label}}` | `Bancolombia Ahorros`        |
| Valor extra          | `{{pago_extra_valor}}` | `12345678901`                |

Cualquier cambio se refleja automáticamente en el PDF de la siguiente cuenta de cobro generada.

### Tipografía configurable

Desde el mismo formulario de empresa hay una sección **Tipografía** con 6 opciones seleccionables visualmente:

| Fuente            | Estilo                                              |
|-------------------|-----------------------------------------------------|
| **Century Gothic** | Geométrica y elegante. Documentos formales        |
| **Inter**         | Moderna y nítida. Apps SaaS                          |
| **Roboto**        | Neutra y muy legible. Google y Android               |
| **Poppins**       | Geométrica amigable y redondeada. Cálida y moderna   |
| **Lato**          | Humanista y cálida. Texto largo y profesional        |
| **Open Sans**     | Clásica, segura y neutral. Muy usada en web          |

La fuente seleccionada se aplica a **toda la app** (interfaz web + PDFs generados). Los archivos `.ttf` están incluidos en `app/static/fonts/` con licencia OFL/Apache, lo que permite que WeasyPrint las embeba directamente en el PDF sin requerir internet en producción.

---

## 🛠 Módulo Infraestructura (Gestión IT por cliente)

Cada cliente puede tener un módulo de "Infraestructura" accesible desde **Clientes → ver cliente → botón "Infraestructura"** (solo visible para administradores).

### Funcionalidades

**Sedes:** un cliente puede tener varias sucursales, cada una con su red independiente. Cada sede tiene dirección, ciudad, responsable y notas.

**Inventario de equipos** (14 tipos predefinidos con íconos):

| Tipo | Uso |
|------|-----|
| 🌐 Internet (WAN/ISP) | conexión del proveedor |
| 🛡 Firewall | filtrado perimetral |
| 📡 Router | enrutamiento |
| 🔌 Switch | conmutación cableada |
| 📶 Access Point | WiFi |
| 🖥 Servidor / NAS | servicios y almacenamiento |
| 🖥 PC / 💻 Portátil | estaciones de trabajo |
| 🖨 Impresora | impresión |
| 📷 Cámara IP / ☎️ Teléfono IP | dispositivos IP |
| 🔋 UPS | respaldo eléctrico |
| 📦 Otro | cualquier otro activo |

Cada equipo guarda: nombre/etiqueta, marca, modelo, IP, MAC, ubicación física, sistema operativo, serial, fecha de instalación, observaciones, y un **equipo padre** (para definir conexiones — base del diagrama futuro).

**Documentos:** sube cualquier archivo (PDF, imágenes, Word, Excel, etc.) asociado al cliente o a una sede específica. Categorías: contrato, manual, factura, diagrama, foto, otro. Sin límite de tamaño.

**Notas rápidas:** comentarios libres con timestamp y autor.

### Almacenamiento de archivos en producción (Railway Volume)

⚠ **Importante:** Railway tiene filesystem efímero (los archivos subidos se borran en cada redeploy). Para que los documentos persistan, necesitas crear un **Railway Volume**:

1. Railway → tu servicio `gestionOne` → **Settings → Volumes → + New Volume**
2. **Mount path:** `/data`
3. **Size:** 1 GB (puedes ampliar luego)

Luego agrega la variable de entorno:
- **`STORAGE_PATH`** = `/data/uploads`

Esto le dice a la app dónde guardar los archivos. Costo aproximado: ~$0.25 USD/GB/mes.

### Próximas entregas previstas

- **Entrega 2:** Credenciales/accesos cifrados ✅
- **Entrega 3:** Diagrama visual interactivo de la red ✅

### 🔐 Credenciales cifradas (Entrega 2)

Desde el hub de Infraestructura puedes acceder al gestor de **credenciales y accesos** del cliente. Funcionalidades:

- **12 categorías** predefinidas (FTP, panel de hosting, cPanel, correo admin, WiFi, RDP/SSH, base de datos, API, CMS, VPN, etc.)
- **Cifrado AES-128** (Fernet) de todas las contraseñas antes de guardarlas en Postgres
- **Botón "mostrar/ocultar"** la contraseña con descifrado al vuelo
- **Botón "copiar"** que copia la contraseña al portapapeles sin mostrarla
- **Cada visualización queda registrada en auditoría** (`ver_credencial`)
- **Solo administradores** pueden ver, editar o eliminar credenciales

#### Configurar la clave de cifrado

Antes de usar el módulo necesitas definir la variable de entorno `ENCRYPTION_KEY` en Railway. Genérala así en tu máquina (UNA sola vez en la vida del proyecto):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copia la salida (algo como `gAAAAA...=`) y pégala en Railway → Variables → `ENCRYPTION_KEY=...`

⚠ **Guarda la clave en un lugar seguro fuera de Railway.** Si pierdes Railway y la clave, las credenciales son irrecuperables. Si rotas la clave, hay que re-cifrar todas las credenciales existentes.

### 🌐 Diagrama de red interactivo (Entrega 3)

Desde el detalle de cada sede hay un botón **"Ver diagrama"** que abre un diagrama interactivo con la topología de red, generado automáticamente a partir del campo "Conectado a" (`padre_id`) de cada equipo.

**Funcionalidades:**

- **Auto-layout jerárquico**: Internet arriba, equipos hojas (PCs/laptops) abajo
- **3 modos de visualización**: vertical, horizontal, libre (drag & drop manual)
- **Click en un nodo**: muestra panel lateral con todos los datos del equipo y botón "Editar"
- **Hover en un nodo**: tooltip con datos completos
- **Zoom + pan** con scroll del mouse
- **Botón "Ajustar"**: centra y encuadra todo el diagrama
- **Colores por tipo**: cada categoría de equipo tiene su color (Internet azul, Router morado, Switch naranja, PC azul, etc.)
- **Detección de equipos huérfanos**: warning si hay equipos sin "Conectado a" definido

**Exportación:**

- **PNG**: descarga el diagrama como imagen
- **PDF**: genera un PDF A4 horizontal con encabezado (nombre de sede, cliente, fecha)

**Tecnología:**

- [vis-network](https://visjs.github.io/vis-network/) (librería de grafos interactivos, ~150KB)
- [jsPDF](https://github.com/parallax/jsPDF) (generación PDF cliente)
- Ambas vía CDN, no requieren instalación adicional

---

## 🚀 Inicio rápido (local)

### 1. Clonar / descomprimir el proyecto y abrir terminal en su carpeta

```bash
cd gestiononeapp
```

### 2. Crear entorno virtual

**Linux / Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> **⚠ Nota sobre WeasyPrint:** requiere librerías nativas del sistema (Cairo, Pango, GObject) para generar PDFs reales. Si no las tienes, la app igual funciona pero entrega un HTML descargable como fallback.
>
> **Instalación de dependencias nativas:**
>
> - **Ubuntu / Debian:**
>   ```bash
>   sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 libgdk-pixbuf-2.0-0
>   ```
> - **Mac (Homebrew):**
>   ```bash
>   brew install pango gdk-pixbuf libffi
>   ```
> - **Windows:** ver [docs WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows) — recomendado usar WSL.
> - **Railway:** las imágenes base ya incluyen estas librerías; funciona out-of-the-box.

### 4. Arrancar

```bash
python wsgi.py
```

Abre tu navegador en **http://127.0.0.1:5000**

**Credenciales demo (creadas automáticamente la primera vez):**
- Usuario: `admin`
- Contraseña: `admin123`
- Empresa: `Mi Empresa S.A.S`

---

## 🌐 Despliegue en Railway

1. **Sube el código a GitHub**
2. **Crea un proyecto nuevo en [Railway](https://railway.app)** y conéctalo a tu repo
3. **Añade un plugin PostgreSQL** (Railway crea la variable `DATABASE_URL` automáticamente)
4. **Variables de entorno opcionales** (en la pestaña *Variables* de tu servicio):
   - `SECRET_KEY` — clave secreta de Flask (genera una nueva en producción)
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_FROM` — config SMTP para el envío de correos
5. **Deploy automático**: el `Procfile` ya contiene el comando con Gunicorn

```
web: gunicorn app:app
```

El `runtime.txt` especifica `python-3.12.4`.

---

## 🏗 Arquitectura del proyecto

```
gestiononeapp/
├── app.py                      # Entry point (crea admin/empresa demo en primer arranque)
├── config.py                   # Configuración dev/prod
├── requirements.txt            # Dependencias
├── Procfile                    # Comando de inicio para Railway
├── runtime.txt                 # Versión de Python
├── .env.example                # Plantilla de variables de entorno
│
├── uploads/                    # Logos de empresas (servidos por la app)
├── exports/                    # Archivos exportados temporales
│
└── app/
    ├── __init__.py             # Application factory + context_processor con modelos
    ├── models.py               # SQLAlchemy: Empresa, Usuario, Cliente, Producto,
    │                           # Cotizacion + DetalleCotizacion, CuentaCobro,
    │                           # PlantillaLayout, RegistroAuditoria
    │
    ├── utils/                  # Helpers reutilizables
    │   ├── decoradores.py      # @rol_requerido, @admin_requerido
    │   ├── filtros.py          # Jinja: |moneda, |fecha_es, |badge_estado
    │   ├── auditoria.py        # registrar_evento()
    │   ├── pdf.py              # WeasyPrint + sustitución de variables {{nombre}}
    │   └── correo.py           # SMTP estándar con adjuntos
    │
    ├── modules/                # Blueprints por dominio
    │   ├── auth/               # login, logout, recuperar, restablecer
    │   ├── dashboard/          # KPIs + gráficas
    │   ├── empresas/           # CRUD + upload de logo
    │   ├── clientes/           # CRUD con HTMX
    │   ├── productos/          # CRUD + API JSON
    │   ├── cotizaciones/       # CRUD + aprobar/anular/pdf/enviar/convertir
    │   ├── cuentas_cobro/      # CRUD + marcar/pdf/enviar
    │   ├── layouts/            # Editor GrapesJS + guardar AJAX
    │   ├── auditoria/          # Lista filtrable (solo admin)
    │   └── usuarios/           # CRUD usuarios con 3 roles
    │
    ├── static/
    │   ├── css/app.css         # Sistema de diseño completo (810 líneas)
    │   └── js/
    │       ├── app.js          # Sidebar toggle, alerts auto-dismiss
    │       ├── cotizacion_form.js   # Filas dinámicas + recálculo
    │       └── layout_designer.js   # Config GrapesJS
    │
    └── templates/              # Plantillas Jinja2
        ├── base.html
        ├── partials/           # sidebar, topbar, paginación
        ├── auth/               # login, recuperar, restablecer
        ├── dashboard/          # index con Chart.js
        ├── clientes/           # lista, _tabla (HTMX), form, detalle
        ├── productos/          # lista, _tabla (HTMX), form
        ├── cotizaciones/       # lista, form, detalle, correo
        ├── cuentas_cobro/      # lista, form, detalle, correo
        ├── empresas/           # lista, form
        ├── usuarios/           # lista, form
        ├── layouts/            # lista, nuevo, editor (GrapesJS)
        ├── auditoria/          # lista filtrable
        └── pdf/                # cotizacion, cuenta_cobro (HTML imprimible)
```

---

## 🔑 Variables de entorno (.env)

Copia `.env.example` a `.env` y ajusta:

```bash
SECRET_KEY=cambia-esto-en-produccion
FLASK_ENV=development
DATABASE_URL=sqlite:///gestionone.db   # En Railway: postgresql://...

# Correo (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-correo@gmail.com
MAIL_PASSWORD=tu-app-password
MAIL_FROM=GestiónOne <noreply@tudominio.com>
```

---

## 👤 Roles del sistema

| Rol             | Puede ver | Puede crear/editar | Puede eliminar | Administración |
|-----------------|-----------|---------------------|----------------|----------------|
| `administrador` | ✅ Todo    | ✅                  | ✅              | ✅ Sí           |
| `vendedor`      | ✅ Todo    | ✅                  | ❌              | ❌ No           |
| `consulta`      | ✅ Todo    | ❌                  | ❌              | ❌ No           |

---

## 🧩 Variables disponibles en el Layout Designer

Al diseñar plantillas PDF en el editor visual, puedes usar estas variables que se reemplazarán automáticamente:

| Variable                  | Cotización | Cuenta de cobro |
|---------------------------|:----------:|:---------------:|
| `{{numero}}`              | ✅         | -                |
| `{{consecutivo}}`         | -          | ✅              |
| `{{fecha}}`               | ✅         | ✅              |
| `{{cliente_nombre}}`      | ✅         | ✅              |
| `{{cliente_nit}}`         | ✅         | ✅              |
| `{{observaciones}}`       | ✅         | -                |
| `{{concepto}}`            | -          | ✅              |
| `{{subtotal}}`            | ✅         | -                |
| `{{iva_total}}`           | ✅         | -                |
| `{{total}}`               | ✅         | -                |
| `{{valor}}`               | -          | ✅              |
| `{{empresa_nombre}}`      | ✅         | ✅              |
| `{{empresa_nit}}`         | ✅         | ✅              |

---

## 🛠 Tecnologías

| Categoría    | Stack                                                         |
|--------------|---------------------------------------------------------------|
| Backend      | Python 3.12, Flask 3.0, SQLAlchemy 2.0, Flask-Login, Flask-Migrate |
| Base de datos| SQLite (dev), PostgreSQL (prod en Railway)                    |
| Frontend     | Bootstrap 5, HTMX, JS Vanilla, Chart.js, GrapesJS, Inter font |
| PDF / Correo | WeasyPrint, SMTP estándar (smtplib)                           |
| Producción   | Gunicorn, Railway                                             |

---

## 📝 Notas finales

- La aplicación crea automáticamente un usuario administrador (`admin/admin123`) y una empresa demo en el primer arranque si no existen.
- Las plantillas personalizadas se almacenan en la base de datos como HTML+CSS+componentes JSON, permitiendo re-edición en GrapesJS.
- WeasyPrint puede no estar disponible en algunas plataformas; en ese caso el PDF se entrega como HTML descargable (el documento sigue siendo imprimible desde el navegador).
- Para producción, **cambia `SECRET_KEY` por una clave fuerte** y usa PostgreSQL en lugar de SQLite.

---

**Desarrollado con ❤ — listo para producción.**
