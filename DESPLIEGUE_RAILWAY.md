# 🚂 Despliegue en Railway — paso a paso

Esta guía asume que ya tienes:
- Una cuenta en [Railway](https://railway.app)
- Un proyecto creado en Railway con una **base de datos PostgreSQL** ya provisionada
- [Git](https://git-scm.com/) instalado localmente
- Una cuenta en [GitHub](https://github.com)

## 1. Sube el código a GitHub

Desde la carpeta `gestiononeapp/`:

```bash
git init
git add .
git commit -m "GestiónOne — primer despliegue"

# Crea un repositorio NUEVO en GitHub (sin README, sin .gitignore)
# Copia la URL HTTPS y reemplázala abajo:
git remote add origin https://github.com/TU_USUARIO/gestiononeapp.git
git branch -M main
git push -u origin main
```

## 2. Conecta el repo con Railway

1. Entra a tu proyecto en Railway (donde ya tienes el PostgreSQL)
2. Click en **"+ New" → "GitHub Repo"**
3. Si es la primera vez, autoriza Railway en GitHub y selecciona el repo `gestiononeapp`
4. Railway empezará a construir automáticamente. **Detenlo con "Stop"** mientras configuramos las variables (paso 3)

## 3. Conecta PostgreSQL a la app

1. En tu servicio de la **app** (no en el de Postgres), ve a la pestaña **"Variables"**
2. Click en **"+ New Variable" → "Add Reference"**
3. Selecciona tu servicio Postgres y la variable **`DATABASE_URL`**
4. Railway la enlaza automáticamente — ya no tienes que copiar/pegar nada

## 4. Configura las variables de entorno restantes

En la misma pestaña **"Variables"** de tu app, añade:

| Variable        | Valor                                            | Descripción                       |
|-----------------|--------------------------------------------------|-----------------------------------|
| `FLASK_ENV`     | `produccion`                                     | Activa config de producción       |
| `SECRET_KEY`    | (genera una clave segura — ver abajo)            | Para firmar sesiones de Flask     |
| `PYTHON_VERSION`| `3.12`                                           | Versión de Python                 |

**Cómo generar un `SECRET_KEY` seguro:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copia la salida (algo como `a7f9c2...`) y pégala como valor de `SECRET_KEY`.

### Variables opcionales (para envío de correos)

Si quieres que tu app envíe cotizaciones por correo, agrega también:

| Variable        | Ejemplo                                  |
|-----------------|------------------------------------------|
| `MAIL_SERVER`   | `smtp.gmail.com`                         |
| `MAIL_PORT`     | `587`                                    |
| `MAIL_USE_TLS`  | `true`                                   |
| `MAIL_USERNAME` | `tucorreo@gmail.com`                     |
| `MAIL_PASSWORD` | (contraseña de aplicación, no tu clave)  |
| `MAIL_DEFAULT_SENDER` | `GestiónOne <tucorreo@gmail.com>`  |

> Para Gmail, debes crear una [contraseña de aplicación](https://myaccount.google.com/apppasswords), no usar tu contraseña normal.

## 5. Despliega

1. Vuelve a la pestaña **"Deployments"** y click en **"Deploy"** (o haz un push a `main` para autodisparar)
2. Espera 2-3 minutos mientras Railway:
   - Instala las librerías nativas (Cairo, Pango, etc. — para WeasyPrint)
   - Instala las dependencias Python
   - Crea las tablas en PostgreSQL automáticamente
   - Inserta empresa demo + usuario `admin / admin123`

## 6. Abre la URL pública

1. Ve a la pestaña **"Settings"** de tu servicio app
2. En la sección **"Networking"** click en **"Generate Domain"**
3. Railway te dará una URL como `https://gestiononeapp-production.up.railway.app`
4. Ábrela y entra con:
   - Usuario: `admin`
   - Contraseña: `admin123`

## 7. Cargar la plantilla "Estilo Verde"

Una vez logeado por primera vez, abre la **consola de Railway** (pestaña "Settings" → "Run a Command") y ejecuta:

```bash
python crear_plantilla_verde.py
```

Esto creará la plantilla PDF con tu firma y la marcará como predeterminada.

## 8. ¡Cambia la contraseña!

**Importante:** entra como `admin` y cambia tu contraseña inmediatamente. La plantilla `admin/admin123` solo es para el primer arranque.

---

## 🛠 Solución de problemas

### "Application error" en la primera carga

Mira los logs en Railway (pestaña "Deployments" → click en el deploy → "View Logs"). Los errores comunes son:

- **`could not connect to server`** → la variable `DATABASE_URL` no está enlazada. Revisa el paso 3.
- **`No module named 'weasyprint'`** → falla en pip install. Verifica que `nixpacks.toml` esté en la raíz del repo.
- **`OSError: cannot load library 'libgobject...'`** → faltan libs nativas. Verifica `nixpacks.toml` (sección `nixPkgs`).

### PDFs se ven sin estilos

WeasyPrint necesita que las fuentes estén accesibles. Verifica que `app/static/fonts/` esté en el repo (ya está incluida en el zip).

### Quiero conectar mi dominio personalizado

En Railway, "Settings" → "Networking" → "Custom Domain". Te dan un registro CNAME para configurar en tu dominio.

### Logo no se sube

Los archivos en `uploads/` son **efímeros en Railway** (se borran al redeploy). Para producción real, deberías usar S3 o Cloudinary. Por ahora funcionará durante una sesión.

---

## 📊 Costos estimados

Railway tiene un free tier de **$5/mes de crédito** para developers nuevos. Una app pequeña como ésta consume aprox:
- App service: ~$2-3/mes
- PostgreSQL: ~$5/mes

Para producción real, considera el plan Hobby ($5/mes adicional) si necesitas más recursos.

---

**¡Listo!** Si tienes algún problema en algún paso, copia el error de los logs de Railway y pídeme ayuda.
