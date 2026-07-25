"""
Modelos de datos de GestiónOne.

Incluye:
  - Usuario          (con login y roles)
  - Empresa          (multiempresa)
  - Cliente
  - Producto
  - Cotizacion + DetalleCotizacion
  - CuentaCobro
  - PlantillaLayout  (diseñador de documentos)
  - RegistroAuditoria
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app import db


# --------------------------------------------------------------------- #
#  EMPRESA (multiempresa)                                               #
# --------------------------------------------------------------------- #
class Empresa(db.Model):
    __tablename__ = "empresas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    nit = db.Column(db.String(40), unique=True, nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(40))
    correo = db.Column(db.String(120))
    logo = db.Column(db.String(255))  # ruta al archivo en /uploads
    # Métodos de pago (visibles en plantillas PDF de cuentas de cobro)
    pago_llave = db.Column(db.String(80))         # P.ej. número de Llave Bancolombia
    pago_daviplata = db.Column(db.String(80))     # Número Daviplata
    pago_nequi = db.Column(db.String(80))         # Número Nequi
    pago_extra_label = db.Column(db.String(50))   # Etiqueta extra opcional (ej: "Banco")
    pago_extra_valor = db.Column(db.String(120))  # Valor del extra (ej: "Bancolombia 0123-456")
    # Tipografía global de la empresa (frontend + PDFs)
    # Valores válidos: century_gothic, inter, roboto, poppins, lato, open_sans
    tipografia = db.Column(db.String(30), default="century_gothic")
    firma = db.Column(db.String(255))  # nombre del archivo de la firma en /uploads
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuarios = db.relationship("Usuario", back_populates="empresa", lazy="dynamic")
    clientes = db.relationship("Cliente", back_populates="empresa", lazy="dynamic")
    productos = db.relationship("Producto", back_populates="empresa", lazy="dynamic")
    cotizaciones = db.relationship("Cotizacion", back_populates="empresa", lazy="dynamic")
    cuentas = db.relationship("CuentaCobro", back_populates="empresa", lazy="dynamic")
    plantillas = db.relationship("PlantillaLayout", back_populates="empresa", lazy="dynamic")

    def __repr__(self):
        return f"<Empresa {self.nombre}>"


# --------------------------------------------------------------------- #
#  USUARIO (con autenticación y roles)                                  #
# --------------------------------------------------------------------- #
class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default="vendedor")  # administrador | vendedor | consulta
    activo = db.Column(db.Boolean, default=True)
    token_reset = db.Column(db.String(255))   # estructura preparada para recuperación
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"))
    empresa = db.relationship("Empresa", back_populates="usuarios")

    # Helpers de contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helpers de rol
    @property
    def es_admin(self):
        return self.rol == "administrador"

    @property
    def puede_editar(self):
        return self.rol in ("administrador", "vendedor")

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"


# --------------------------------------------------------------------- #
#  CLIENTE                                                              #
# --------------------------------------------------------------------- #
class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False, index=True)
    nit = db.Column(db.String(40), index=True)
    direccion = db.Column(db.String(200))
    ciudad = db.Column(db.String(80))
    telefono = db.Column(db.String(40))
    correo = db.Column(db.String(120))
    estado = db.Column(db.String(20), default="activo")   # activo | inactivo
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    empresa = db.relationship("Empresa", back_populates="clientes")

    cotizaciones = db.relationship("Cotizacion", back_populates="cliente", lazy="dynamic")
    cuentas = db.relationship("CuentaCobro", back_populates="cliente", lazy="dynamic")

    def __repr__(self):
        return f"<Cliente {self.nombre}>"


# --------------------------------------------------------------------- #
#  PRODUCTO                                                             #
# --------------------------------------------------------------------- #
class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), unique=True, index=True)
    nombre = db.Column(db.String(150), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, default=0.0)
    iva = db.Column(db.Float, default=19.0)   # porcentaje
    estado = db.Column(db.String(20), default="activo")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    empresa = db.relationship("Empresa", back_populates="productos")

    def __repr__(self):
        return f"<Producto {self.codigo} - {self.nombre}>"


# --------------------------------------------------------------------- #
#  COTIZACION                                                           #
# --------------------------------------------------------------------- #
class Cotizacion(db.Model):
    __tablename__ = "cotizaciones"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, index=True)  # COT-000001
    fecha = db.Column(db.Date, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(20), default="borrador")  # borrador | aprobada | anulada
    subtotal = db.Column(db.Float, default=0.0)
    iva_total = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="cotizaciones")

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    empresa = db.relationship("Empresa", back_populates="cotizaciones")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    usuario = db.relationship("Usuario")

    detalles = db.relationship(
        "DetalleCotizacion",
        back_populates="cotizacion",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def recalcular_totales(self):
        """Recalcula subtotal, iva y total a partir de los detalles."""
        sub = sum(d.cantidad * d.valor_unitario for d in self.detalles)
        iva = sum(
            d.cantidad * d.valor_unitario * (d.iva / 100.0) for d in self.detalles
        )
        self.subtotal = round(sub, 2)
        self.iva_total = round(iva, 2)
        self.total = round(sub + iva, 2)

    def __repr__(self):
        return f"<Cotizacion {self.numero}>"


class DetalleCotizacion(db.Model):
    __tablename__ = "detalle_cotizacion"

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"))
    descripcion = db.Column(db.String(255))
    cantidad = db.Column(db.Float, default=1.0)
    valor_unitario = db.Column(db.Float, default=0.0)
    iva = db.Column(db.Float, default=19.0)

    cotizacion = db.relationship("Cotizacion", back_populates="detalles")
    producto = db.relationship("Producto")

    @property
    def subtotal(self):
        return round(self.cantidad * self.valor_unitario, 2)

    @property
    def total(self):
        return round(self.subtotal * (1 + self.iva / 100.0), 2)


# --------------------------------------------------------------------- #
#  CUENTA DE COBRO                                                      #
# --------------------------------------------------------------------- #
class CuentaCobro(db.Model):
    __tablename__ = "cuentas_cobro"

    id = db.Column(db.Integer, primary_key=True)
    consecutivo = db.Column(db.String(20), unique=True, index=True)  # CC-000001
    fecha = db.Column(db.Date, default=datetime.utcnow)
    concepto = db.Column(db.Text)
    valor = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente | pagada | anulada
    fecha_pago = db.Column(db.Date)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="cuentas")

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    empresa = db.relationship("Empresa", back_populates="cuentas")

    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"))
    cotizacion = db.relationship("Cotizacion")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<CuentaCobro {self.consecutivo}>"


# --------------------------------------------------------------------- #
#  PLANTILLA LAYOUT (diseñador de documentos)                            #
# --------------------------------------------------------------------- #
class PlantillaLayout(db.Model):
    __tablename__ = "plantillas_layout"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(30), default="cotizacion")  # cotizacion | cuenta_cobro
    html_contenido = db.Column(db.Text)      # HTML producido por GrapesJS
    css_contenido = db.Column(db.Text)       # CSS producido por GrapesJS
    componentes_json = db.Column(db.Text)    # JSON de componentes (para re-edición)
    estilos_json = db.Column(db.Text)        # JSON de estilos
    es_predeterminada = db.Column(db.Boolean, default=False)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    empresa = db.relationship("Empresa", back_populates="plantillas")

    def __repr__(self):
        return f"<PlantillaLayout {self.nombre} ({self.tipo})>"


# --------------------------------------------------------------------- #
#  AUDITORÍA                                                             #
# --------------------------------------------------------------------- #
class RegistroAuditoria(db.Model):
    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    usuario_nombre = db.Column(db.String(150))  # snapshot por si se borra el usuario
    accion = db.Column(db.String(40))      # crear | editar | eliminar | exportar_pdf | enviar_correo | login | logout
    modulo = db.Column(db.String(60))      # clientes | productos | ...
    descripcion = db.Column(db.Text)
    ip = db.Column(db.String(45))
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<Auditoria {self.accion} {self.modulo}>"


# ============================================================================
#  MÓDULO DE INFRAESTRUCTURA — gestión IT del cliente
# ============================================================================

class Sede(db.Model):
    """Sucursal o sede física de un cliente, con su propia red independiente."""
    __tablename__ = "sedes"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(200))
    ciudad = db.Column(db.String(80))
    telefono = db.Column(db.String(40))
    responsable = db.Column(db.String(150))         # contacto principal en la sede
    notas = db.Column(db.Text)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = db.relationship("Cliente", backref=db.backref("sedes", lazy="dynamic", cascade="all, delete-orphan"))
    equipos = db.relationship("Equipo", backref="sede", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def total_equipos(self):
        return self.equipos.count()

    def __repr__(self):
        return f"<Sede {self.nombre}>"


class Equipo(db.Model):
    """Equipo / activo de la infraestructura de red de una sede."""
    __tablename__ = "equipos"

    # Tipos soportados (alineados con los íconos del frontend)
    TIPOS = (
        "internet", "firewall", "router", "switch", "ap",
        "servidor", "nas", "pc", "portatil", "impresora",
        "camara_ip", "telefono_ip", "ups", "otro",
    )

    id = db.Column(db.Integer, primary_key=True)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=False, index=True)
    tipo = db.Column(db.String(30), nullable=False, default="otro")
    nombre = db.Column(db.String(120), nullable=False)        # ej: "SW-PISO-2", "Router principal"
    marca = db.Column(db.String(80))
    modelo = db.Column(db.String(120))
    ip = db.Column(db.String(45))                              # IPv4 o IPv6
    mac = db.Column(db.String(32))
    ubicacion_fisica = db.Column(db.String(150))               # "Rack 2, U-12" / "Oficina 305"
    sistema_operativo = db.Column(db.String(80))               # solo aplica a servidores/PC
    serial = db.Column(db.String(120))
    fecha_instalacion = db.Column(db.Date)
    observaciones = db.Column(db.Text)

    # Para el diagrama: este equipo "cuelga" de otro (ej. una PC conectada a un switch)
    padre_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=True, index=True)
    padre = db.relationship("Equipo", remote_side=[id], backref=db.backref("hijos", lazy="dynamic"))

    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def tipo_label(self):
        labels = {
            "internet": "Internet (WAN/ISP)",
            "firewall": "Firewall",
            "router": "Router",
            "switch": "Switch",
            "ap": "Access Point",
            "servidor": "Servidor",
            "nas": "NAS / Storage",
            "pc": "PC de escritorio",
            "portatil": "Portátil",
            "impresora": "Impresora",
            "camara_ip": "Cámara IP",
            "telefono_ip": "Teléfono IP",
            "ups": "UPS",
            "otro": "Otro",
        }
        return labels.get(self.tipo, self.tipo.title())

    @property
    def tipo_icono(self):
        """Clase de Bootstrap Icons asociada al tipo."""
        iconos = {
            "internet": "bi-globe2",
            "firewall": "bi-shield-lock-fill",
            "router": "bi-router-fill",
            "switch": "bi-hdd-network-fill",
            "ap": "bi-wifi",
            "servidor": "bi-server",
            "nas": "bi-hdd-stack-fill",
            "pc": "bi-pc-display",
            "portatil": "bi-laptop",
            "impresora": "bi-printer-fill",
            "camara_ip": "bi-camera-video-fill",
            "telefono_ip": "bi-telephone-fill",
            "ups": "bi-battery-charging",
            "otro": "bi-box",
        }
        return iconos.get(self.tipo, "bi-box")

    def __repr__(self):
        return f"<Equipo {self.tipo}:{self.nombre}>"


class Documento(db.Model):
    """Archivo subido relacionado a un cliente (y opcionalmente a una sede)."""
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=True, index=True)
    nombre = db.Column(db.String(200), nullable=False)         # nombre para mostrar
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(60), default="otro")       # contrato | manual | factura | diagrama | foto | otro
    archivo_path = db.Column(db.String(500), nullable=False)   # ruta relativa al volumen
    tamanio_bytes = db.Column(db.BigInteger, default=0)
    mime_type = db.Column(db.String(100))
    subido_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", backref=db.backref("documentos", lazy="dynamic", cascade="all, delete-orphan"))
    sede = db.relationship("Sede", backref=db.backref("documentos", lazy="dynamic"))
    usuario = db.relationship("Usuario")

    @property
    def tamanio_legible(self):
        """Devuelve el tamaño en formato humano: 1.2 MB, 340 KB, etc."""
        b = self.tamanio_bytes or 0
        for unidad in ("B", "KB", "MB", "GB", "TB"):
            if b < 1024:
                return f"{b:.1f} {unidad}".replace(".0 ", " ")
            b /= 1024
        return f"{b:.1f} PB"

    @property
    def extension(self):
        return (self.archivo_path or "").rsplit(".", 1)[-1].lower() if "." in (self.archivo_path or "") else ""

    @property
    def es_imagen(self):
        return self.extension in ("png", "jpg", "jpeg", "gif", "webp", "svg")

    @property
    def es_pdf(self):
        return self.extension == "pdf"

    def __repr__(self):
        return f"<Documento {self.nombre}>"


class NotaCliente(db.Model):
    """Nota libre con timestamp asociada a un cliente."""
    __tablename__ = "notas_cliente"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)
    contenido = db.Column(db.Text, nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    cliente = db.relationship("Cliente", backref=db.backref("notas", lazy="dynamic", cascade="all, delete-orphan",
                                                            order_by="NotaCliente.creada_en.desc()"))
    autor = db.relationship("Usuario")

    def __repr__(self):
        return f"<NotaCliente cliente={self.cliente_id}>"


class Credencial(db.Model):
    """
    Credencial / acceso a una plataforma del cliente.
    La contraseña se guarda CIFRADA (Fernet/AES-128). Solo el admin puede verla.
    """
    __tablename__ = "credenciales"

    # Categorías soportadas
    CATEGORIAS = (
        "ftp", "panel_hosting", "panel_dominio", "correo_admin",
        "wifi", "rdp_ssh", "base_datos", "api",
        "cms", "servicio_externo", "vpn", "otro",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=True, index=True)
    categoria = db.Column(db.String(30), nullable=False, default="otro")
    nombre = db.Column(db.String(150), nullable=False)         # "FTP Hosting Principal"
    url = db.Column(db.String(300))                            # "ftp.midominio.com"
    puerto = db.Column(db.String(10))                          # "21", "22", "3306"...
    usuario = db.Column(db.String(150))                        # texto plano, no es secreto
    password_cifrado = db.Column(db.Text)                      # texto cifrado en base64
    notas = db.Column(db.Text)                                 # comentarios libres

    creada_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = db.relationship("Cliente", backref=db.backref("credenciales", lazy="dynamic", cascade="all, delete-orphan"))
    sede = db.relationship("Sede", backref=db.backref("credenciales", lazy="dynamic"))
    autor = db.relationship("Usuario")

    @property
    def categoria_label(self):
        labels = {
            "ftp": "FTP / SFTP",
            "panel_hosting": "Panel de hosting (cPanel, Plesk)",
            "panel_dominio": "Panel de dominio (DNS)",
            "correo_admin": "Correo administrador",
            "wifi": "Red WiFi",
            "rdp_ssh": "Acceso remoto (RDP / SSH)",
            "base_datos": "Base de datos",
            "api": "API / Token",
            "cms": "CMS (WordPress, Drupal, etc.)",
            "servicio_externo": "Servicio externo (SaaS)",
            "vpn": "VPN",
            "otro": "Otro",
        }
        return labels.get(self.categoria, self.categoria.title())

    @property
    def categoria_icono(self):
        iconos = {
            "ftp": "bi-cloud-upload-fill",
            "panel_hosting": "bi-hdd-rack-fill",
            "panel_dominio": "bi-globe2",
            "correo_admin": "bi-envelope-fill",
            "wifi": "bi-wifi",
            "rdp_ssh": "bi-terminal-fill",
            "base_datos": "bi-database-fill",
            "api": "bi-braces",
            "cms": "bi-window-stack",
            "servicio_externo": "bi-box-arrow-up-right",
            "vpn": "bi-shield-shaded",
            "otro": "bi-key-fill",
        }
        return iconos.get(self.categoria, "bi-key-fill")

    @property
    def categoria_color(self):
        """Color del chip de categoría en la UI."""
        colores = {
            "ftp": "#06b6d4",
            "panel_hosting": "#8b5cf6",
            "panel_dominio": "#3b82f6",
            "correo_admin": "#ec4899",
            "wifi": "#10b981",
            "rdp_ssh": "#1f2937",
            "base_datos": "#f59e0b",
            "api": "#6366f1",
            "cms": "#0ea5e9",
            "servicio_externo": "#f97316",
            "vpn": "#16a34a",
            "otro": "#64748b",
        }
        return colores.get(self.categoria, "#64748b")

    def __repr__(self):
        return f"<Credencial {self.categoria}:{self.nombre}>"
