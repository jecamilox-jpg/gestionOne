"""
Módulo de Infraestructura — gestión IT por cliente.

Estructura de URLs:
  /clientes/<id>/infraestructura                  → hub general del cliente
  /clientes/<id>/infraestructura/sedes/nueva
  /clientes/<id>/infraestructura/sedes/<sid>      → detalle de sede + equipos
  /clientes/<id>/infraestructura/sedes/<sid>/editar
  /clientes/<id>/infraestructura/sedes/<sid>/eliminar
  /sedes/<sid>/equipos/nuevo                       → CRUD equipos
  /sedes/<sid>/equipos/<eid>/editar
  /sedes/<sid>/equipos/<eid>/eliminar
  /clientes/<id>/infraestructura/documentos       → subir/listar
  /clientes/<id>/infraestructura/documentos/<did>/descargar
  /clientes/<id>/infraestructura/documentos/<did>/eliminar
  /clientes/<id>/infraestructura/notas            → crear nota
  /clientes/<id>/infraestructura/notas/<nid>/eliminar
"""
import os
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    send_file, abort, current_app, jsonify,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Cliente, Sede, Equipo, Documento, NotaCliente
from app.utils.decoradores import admin_requerido
from app.utils.auditoria import registrar_evento

infra_bp = Blueprint("infraestructura", __name__)


# ============================================================================
#  HELPERS
# ============================================================================

def _cliente_o_404(cliente_id):
    """Obtiene un cliente de la empresa actual o 404."""
    return Cliente.query.filter_by(
        id=cliente_id, empresa_id=current_user.empresa_id
    ).first_or_404()


def _sede_o_404(sede_id):
    """Obtiene una sede cuyo cliente pertenezca a la empresa actual."""
    sede = Sede.query.filter_by(id=sede_id).first_or_404()
    if sede.cliente.empresa_id != current_user.empresa_id:
        abort(404)
    return sede


def _equipo_o_404(equipo_id):
    equipo = Equipo.query.filter_by(id=equipo_id).first_or_404()
    if equipo.sede.cliente.empresa_id != current_user.empresa_id:
        abort(404)
    return equipo


def _ruta_uploads_cliente(cliente_id):
    """
    Devuelve la ruta donde guardar archivos de un cliente.
    Usa el volumen montado en /data si existe (Railway), si no /uploads local.
    """
    base = os.environ.get("STORAGE_PATH", "/data/uploads")
    # Fallback a uploads local si /data no existe (desarrollo)
    if not os.path.isdir(os.path.dirname(base)) and not os.environ.get("STORAGE_PATH"):
        base = os.path.join(current_app.root_path, "..", "uploads")
    ruta = os.path.join(base, f"cliente_{cliente_id}")
    os.makedirs(ruta, exist_ok=True)
    return ruta


# ============================================================================
#  HUB GENERAL DEL CLIENTE
# ============================================================================

@infra_bp.route("/clientes/<int:cliente_id>/infraestructura")
@login_required
@admin_requerido
def hub(cliente_id):
    """Vista resumen del módulo de infraestructura para un cliente."""
    cliente = _cliente_o_404(cliente_id)

    sedes = cliente.sedes.order_by(Sede.nombre).all()
    documentos = (cliente.documentos
                  .order_by(Documento.creado_en.desc())
                  .limit(10).all())
    notas = cliente.notas.limit(10).all()

    total_equipos = sum(s.total_equipos for s in sedes)
    total_documentos = cliente.documentos.count()
    total_credenciales = cliente.credenciales.count()

    # Conteo de equipos por tipo (para mostrar resumen visual)
    equipos_por_tipo = (
        db.session.query(Equipo.tipo, db.func.count(Equipo.id))
        .join(Sede).filter(Sede.cliente_id == cliente_id)
        .group_by(Equipo.tipo).all()
    )

    return render_template(
        "infraestructura/hub.html",
        cliente=cliente,
        sedes=sedes,
        documentos=documentos,
        notas=notas,
        total_equipos=total_equipos,
        total_documentos=total_documentos,
        total_credenciales=total_credenciales,
        total_sedes=len(sedes),
        equipos_por_tipo=dict(equipos_por_tipo),
    )


# ============================================================================
#  SEDES
# ============================================================================

@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/sedes/nueva",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def sede_nueva(cliente_id):
    cliente = _cliente_o_404(cliente_id)
    if request.method == "POST":
        sede = Sede(
            cliente_id=cliente.id,
            nombre=request.form["nombre"].strip(),
            direccion=request.form.get("direccion", "").strip(),
            ciudad=request.form.get("ciudad", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            responsable=request.form.get("responsable", "").strip(),
            notas=request.form.get("notas", "").strip(),
        )
        db.session.add(sede)
        db.session.commit()
        registrar_evento("crear", "infraestructura",
                         f"Sede '{sede.nombre}' creada para cliente {cliente.nombre}")
        flash(f"Sede '{sede.nombre}' creada correctamente.", "success")
        return redirect(url_for("infraestructura.sede_detalle",
                                cliente_id=cliente.id, sede_id=sede.id))

    return render_template("infraestructura/sede_form.html",
                           cliente=cliente, sede=None)


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/sedes/<int:sede_id>")
@login_required
@admin_requerido
def sede_detalle(cliente_id, sede_id):
    cliente = _cliente_o_404(cliente_id)
    sede = _sede_o_404(sede_id)
    if sede.cliente_id != cliente.id:
        abort(404)
    equipos = sede.equipos.order_by(Equipo.tipo, Equipo.nombre).all()
    # Para el dropdown "padre" en el form de equipos (lo usaremos en la entrega 3 del diagrama)
    return render_template("infraestructura/sede_detalle.html",
                           cliente=cliente, sede=sede, equipos=equipos)


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/sedes/<int:sede_id>/editar",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def sede_editar(cliente_id, sede_id):
    cliente = _cliente_o_404(cliente_id)
    sede = _sede_o_404(sede_id)
    if sede.cliente_id != cliente.id:
        abort(404)

    if request.method == "POST":
        sede.nombre = request.form["nombre"].strip()
        sede.direccion = request.form.get("direccion", "").strip()
        sede.ciudad = request.form.get("ciudad", "").strip()
        sede.telefono = request.form.get("telefono", "").strip()
        sede.responsable = request.form.get("responsable", "").strip()
        sede.notas = request.form.get("notas", "").strip()
        db.session.commit()
        registrar_evento("editar", "infraestructura", f"Sede '{sede.nombre}' editada")
        flash("Sede actualizada.", "success")
        return redirect(url_for("infraestructura.sede_detalle",
                                cliente_id=cliente.id, sede_id=sede.id))

    return render_template("infraestructura/sede_form.html",
                           cliente=cliente, sede=sede)


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/sedes/<int:sede_id>/eliminar",
                methods=["POST"])
@login_required
@admin_requerido
def sede_eliminar(cliente_id, sede_id):
    cliente = _cliente_o_404(cliente_id)
    sede = _sede_o_404(sede_id)
    if sede.cliente_id != cliente.id:
        abort(404)
    nombre = sede.nombre
    db.session.delete(sede)
    db.session.commit()
    registrar_evento("eliminar", "infraestructura",
                     f"Sede '{nombre}' eliminada del cliente {cliente.nombre}")
    flash(f"Sede '{nombre}' eliminada.", "success")
    return redirect(url_for("infraestructura.hub", cliente_id=cliente.id))


# ============================================================================
#  EQUIPOS
# ============================================================================

@infra_bp.route("/sedes/<int:sede_id>/equipos/nuevo", methods=["GET", "POST"])
@login_required
@admin_requerido
def equipo_nuevo(sede_id):
    sede = _sede_o_404(sede_id)
    if request.method == "POST":
        equipo = Equipo(sede_id=sede.id, **_extraer_form_equipo(request.form))
        db.session.add(equipo)
        db.session.commit()
        registrar_evento("crear", "infraestructura",
                         f"Equipo '{equipo.nombre}' ({equipo.tipo_label}) creado en {sede.nombre}")
        flash(f"Equipo '{equipo.nombre}' creado.", "success")
        return redirect(url_for("infraestructura.sede_detalle",
                                cliente_id=sede.cliente_id, sede_id=sede.id))

    posibles_padres = sede.equipos.order_by(Equipo.nombre).all()
    return render_template("infraestructura/equipo_form.html",
                           sede=sede, equipo=None,
                           tipos=Equipo.TIPOS, posibles_padres=posibles_padres)


@infra_bp.route("/sedes/<int:sede_id>/equipos/<int:equipo_id>/editar",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def equipo_editar(sede_id, equipo_id):
    sede = _sede_o_404(sede_id)
    equipo = _equipo_o_404(equipo_id)
    if equipo.sede_id != sede.id:
        abort(404)

    if request.method == "POST":
        datos = _extraer_form_equipo(request.form)
        for k, v in datos.items():
            setattr(equipo, k, v)
        db.session.commit()
        registrar_evento("editar", "infraestructura", f"Equipo '{equipo.nombre}' editado")
        flash("Equipo actualizado.", "success")
        return redirect(url_for("infraestructura.sede_detalle",
                                cliente_id=sede.cliente_id, sede_id=sede.id))

    # Excluir el equipo actual de la lista de posibles padres (no puede ser padre de sí mismo)
    posibles_padres = sede.equipos.filter(Equipo.id != equipo.id).order_by(Equipo.nombre).all()
    return render_template("infraestructura/equipo_form.html",
                           sede=sede, equipo=equipo,
                           tipos=Equipo.TIPOS, posibles_padres=posibles_padres)


@infra_bp.route("/sedes/<int:sede_id>/equipos/<int:equipo_id>/eliminar",
                methods=["POST"])
@login_required
@admin_requerido
def equipo_eliminar(sede_id, equipo_id):
    sede = _sede_o_404(sede_id)
    equipo = _equipo_o_404(equipo_id)
    if equipo.sede_id != sede.id:
        abort(404)
    nombre = equipo.nombre
    db.session.delete(equipo)
    db.session.commit()
    registrar_evento("eliminar", "infraestructura", f"Equipo '{nombre}' eliminado")
    flash(f"Equipo '{nombre}' eliminado.", "success")
    return redirect(url_for("infraestructura.sede_detalle",
                            cliente_id=sede.cliente_id, sede_id=sede.id))


def _extraer_form_equipo(form):
    """Lee los campos del formulario de equipo y los devuelve como dict."""
    tipo = form.get("tipo", "otro").strip().lower()
    if tipo not in Equipo.TIPOS:
        tipo = "otro"
    fecha = form.get("fecha_instalacion", "").strip()
    fecha_parsed = None
    if fecha:
        try:
            fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            fecha_parsed = None
    padre_id_raw = form.get("padre_id", "").strip()
    padre_id = int(padre_id_raw) if padre_id_raw.isdigit() else None

    return dict(
        tipo=tipo,
        nombre=form["nombre"].strip(),
        marca=form.get("marca", "").strip() or None,
        modelo=form.get("modelo", "").strip() or None,
        ip=form.get("ip", "").strip() or None,
        mac=form.get("mac", "").strip() or None,
        ubicacion_fisica=form.get("ubicacion_fisica", "").strip() or None,
        sistema_operativo=form.get("sistema_operativo", "").strip() or None,
        serial=form.get("serial", "").strip() or None,
        fecha_instalacion=fecha_parsed,
        observaciones=form.get("observaciones", "").strip() or None,
        padre_id=padre_id,
    )


# ============================================================================
#  DOCUMENTOS
# ============================================================================

@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/documentos",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def documentos(cliente_id):
    cliente = _cliente_o_404(cliente_id)

    if request.method == "POST":
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            flash("Debes seleccionar un archivo.", "warning")
            return redirect(url_for("infraestructura.documentos", cliente_id=cliente.id))

        filename = secure_filename(archivo.filename)
        if not filename:
            flash("Nombre de archivo no válido.", "danger")
            return redirect(url_for("infraestructura.documentos", cliente_id=cliente.id))

        # Renombrar con timestamp para evitar colisiones
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename_final = f"{timestamp}-{filename}"
        ruta_dir = _ruta_uploads_cliente(cliente.id)
        ruta_completa = os.path.join(ruta_dir, filename_final)
        archivo.save(ruta_completa)

        # Calcular tamaño
        tam = os.path.getsize(ruta_completa)

        sede_id_raw = request.form.get("sede_id", "").strip()
        sede_id = int(sede_id_raw) if sede_id_raw.isdigit() else None

        doc = Documento(
            cliente_id=cliente.id,
            sede_id=sede_id,
            nombre=request.form.get("nombre", "").strip() or archivo.filename,
            descripcion=request.form.get("descripcion", "").strip() or None,
            categoria=request.form.get("categoria", "otro").strip(),
            archivo_path=os.path.relpath(ruta_completa, os.environ.get("STORAGE_PATH", "/data/uploads")
                                         if os.environ.get("STORAGE_PATH")
                                         else os.path.join(current_app.root_path, "..", "uploads")),
            tamanio_bytes=tam,
            mime_type=archivo.mimetype,
            subido_por=current_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        registrar_evento("crear", "infraestructura",
                         f"Documento '{doc.nombre}' subido ({doc.tamanio_legible})")
        flash(f"Archivo '{doc.nombre}' subido correctamente.", "success")
        return redirect(url_for("infraestructura.documentos", cliente_id=cliente.id))

    documentos = cliente.documentos.order_by(Documento.creado_en.desc()).all()
    sedes = cliente.sedes.order_by(Sede.nombre).all()
    return render_template("infraestructura/documentos.html",
                           cliente=cliente, documentos=documentos, sedes=sedes)


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/documentos/<int:doc_id>/descargar")
@login_required
@admin_requerido
def documento_descargar(cliente_id, doc_id):
    cliente = _cliente_o_404(cliente_id)
    doc = Documento.query.filter_by(id=doc_id, cliente_id=cliente.id).first_or_404()

    # Reconstruir ruta absoluta
    base = os.environ.get("STORAGE_PATH") or os.path.join(current_app.root_path, "..", "uploads")
    ruta = os.path.join(base, doc.archivo_path)
    if not os.path.isfile(ruta):
        flash("El archivo no se encuentra en el almacenamiento.", "danger")
        return redirect(url_for("infraestructura.documentos", cliente_id=cliente.id))

    registrar_evento("descargar", "infraestructura", f"Documento '{doc.nombre}' descargado")
    return send_file(ruta, as_attachment=True, download_name=doc.nombre)


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/documentos/<int:doc_id>/eliminar",
                methods=["POST"])
@login_required
@admin_requerido
def documento_eliminar(cliente_id, doc_id):
    cliente = _cliente_o_404(cliente_id)
    doc = Documento.query.filter_by(id=doc_id, cliente_id=cliente.id).first_or_404()

    # Borrar el archivo del disco
    base = os.environ.get("STORAGE_PATH") or os.path.join(current_app.root_path, "..", "uploads")
    ruta = os.path.join(base, doc.archivo_path)
    try:
        if os.path.isfile(ruta):
            os.remove(ruta)
    except Exception as e:
        current_app.logger.warning(f"No se pudo borrar el archivo {ruta}: {e}")

    nombre = doc.nombre
    db.session.delete(doc)
    db.session.commit()
    registrar_evento("eliminar", "infraestructura", f"Documento '{nombre}' eliminado")
    flash(f"Documento '{nombre}' eliminado.", "success")
    return redirect(url_for("infraestructura.documentos", cliente_id=cliente.id))


# ============================================================================
#  NOTAS
# ============================================================================

@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/notas",
                methods=["POST"])
@login_required
@admin_requerido
def nota_crear(cliente_id):
    cliente = _cliente_o_404(cliente_id)
    contenido = request.form.get("contenido", "").strip()
    if not contenido:
        flash("La nota no puede estar vacía.", "warning")
        return redirect(url_for("infraestructura.hub", cliente_id=cliente.id))

    nota = NotaCliente(
        cliente_id=cliente.id,
        contenido=contenido,
        autor_id=current_user.id,
    )
    db.session.add(nota)
    db.session.commit()
    registrar_evento("crear", "infraestructura", f"Nota agregada al cliente {cliente.nombre}")
    flash("Nota agregada.", "success")
    return redirect(url_for("infraestructura.hub", cliente_id=cliente.id))


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/notas/<int:nota_id>/eliminar",
                methods=["POST"])
@login_required
@admin_requerido
def nota_eliminar(cliente_id, nota_id):
    cliente = _cliente_o_404(cliente_id)
    nota = NotaCliente.query.filter_by(id=nota_id, cliente_id=cliente.id).first_or_404()
    db.session.delete(nota)
    db.session.commit()
    registrar_evento("eliminar", "infraestructura", f"Nota eliminada del cliente {cliente.nombre}")
    flash("Nota eliminada.", "success")
    return redirect(url_for("infraestructura.hub", cliente_id=cliente.id))


# ============================================================================
#  CREDENCIALES (con cifrado AES)
# ============================================================================

from app.models import Credencial
from app.utils.cifrado import cifrar, descifrar, esta_configurado, CifradoNoConfigurado


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/credenciales")
@login_required
@admin_requerido
def credenciales(cliente_id):
    cliente = _cliente_o_404(cliente_id)
    credenciales = (cliente.credenciales
                    .order_by(Credencial.categoria, Credencial.nombre)
                    .all())
    sedes = cliente.sedes.order_by(Sede.nombre).all()
    return render_template(
        "infraestructura/credenciales.html",
        cliente=cliente,
        credenciales=credenciales,
        sedes=sedes,
        categorias=Credencial.CATEGORIAS,
        cifrado_ok=esta_configurado(),
    )


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/credenciales/nueva",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def credencial_nueva(cliente_id):
    cliente = _cliente_o_404(cliente_id)
    if not esta_configurado():
        flash("El cifrado no está configurado. Define la variable ENCRYPTION_KEY antes de crear credenciales.",
              "danger")
        return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))

    if request.method == "POST":
        password_plano = request.form.get("password", "")
        try:
            password_cifrado = cifrar(password_plano) if password_plano else ""
        except CifradoNoConfigurado as e:
            flash(str(e), "danger")
            return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))

        sede_id_raw = request.form.get("sede_id", "").strip()
        sede_id = int(sede_id_raw) if sede_id_raw.isdigit() else None

        cred = Credencial(
            cliente_id=cliente.id,
            sede_id=sede_id,
            categoria=request.form.get("categoria", "otro").strip(),
            nombre=request.form["nombre"].strip(),
            url=request.form.get("url", "").strip() or None,
            puerto=request.form.get("puerto", "").strip() or None,
            usuario=request.form.get("usuario", "").strip() or None,
            password_cifrado=password_cifrado,
            notas=request.form.get("notas", "").strip() or None,
            creada_por=current_user.id,
        )
        db.session.add(cred)
        db.session.commit()
        registrar_evento("crear", "infraestructura",
                         f"Credencial '{cred.nombre}' ({cred.categoria_label}) creada")
        flash(f"Credencial '{cred.nombre}' creada y cifrada.", "success")
        return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))

    sedes = cliente.sedes.order_by(Sede.nombre).all()
    return render_template(
        "infraestructura/credencial_form.html",
        cliente=cliente, credencial=None,
        categorias=Credencial.CATEGORIAS, sedes=sedes,
    )


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/credenciales/<int:cred_id>/editar",
                methods=["GET", "POST"])
@login_required
@admin_requerido
def credencial_editar(cliente_id, cred_id):
    cliente = _cliente_o_404(cliente_id)
    cred = Credencial.query.filter_by(id=cred_id, cliente_id=cliente.id).first_or_404()
    if not esta_configurado():
        flash("El cifrado no está configurado.", "danger")
        return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))

    if request.method == "POST":
        cred.categoria = request.form.get("categoria", "otro").strip()
        cred.nombre = request.form["nombre"].strip()
        cred.url = request.form.get("url", "").strip() or None
        cred.puerto = request.form.get("puerto", "").strip() or None
        cred.usuario = request.form.get("usuario", "").strip() or None
        cred.notas = request.form.get("notas", "").strip() or None

        sede_id_raw = request.form.get("sede_id", "").strip()
        cred.sede_id = int(sede_id_raw) if sede_id_raw.isdigit() else None

        # Solo actualizar password si se proporciona uno nuevo (no vacío)
        password_nuevo = request.form.get("password", "")
        if password_nuevo:
            cred.password_cifrado = cifrar(password_nuevo)

        db.session.commit()
        registrar_evento("editar", "infraestructura", f"Credencial '{cred.nombre}' editada")
        flash("Credencial actualizada.", "success")
        return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))

    sedes = cliente.sedes.order_by(Sede.nombre).all()
    return render_template(
        "infraestructura/credencial_form.html",
        cliente=cliente, credencial=cred,
        categorias=Credencial.CATEGORIAS, sedes=sedes,
    )


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/credenciales/<int:cred_id>/eliminar",
                methods=["POST"])
@login_required
@admin_requerido
def credencial_eliminar(cliente_id, cred_id):
    cliente = _cliente_o_404(cliente_id)
    cred = Credencial.query.filter_by(id=cred_id, cliente_id=cliente.id).first_or_404()
    nombre = cred.nombre
    db.session.delete(cred)
    db.session.commit()
    registrar_evento("eliminar", "infraestructura", f"Credencial '{nombre}' eliminada")
    flash(f"Credencial '{nombre}' eliminada.", "success")
    return redirect(url_for("infraestructura.credenciales", cliente_id=cliente.id))


@infra_bp.route("/clientes/<int:cliente_id>/infraestructura/credenciales/<int:cred_id>/revelar",
                methods=["POST"])
@login_required
@admin_requerido
def credencial_revelar(cliente_id, cred_id):
    """
    Endpoint AJAX que descifra y devuelve la contraseña al cliente.
    Solo accesible vía POST (para evitar accidentes con prefetch o logs de GET).
    """
    cliente = _cliente_o_404(cliente_id)
    cred = Credencial.query.filter_by(id=cred_id, cliente_id=cliente.id).first_or_404()
    if not esta_configurado():
        return jsonify({"ok": False, "error": "Cifrado no configurado"}), 400

    try:
        password = descifrar(cred.password_cifrado) if cred.password_cifrado else ""
    except CifradoNoConfigurado as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    # Auditar la revelación
    registrar_evento("ver_credencial", "infraestructura",
                     f"Contraseña de '{cred.nombre}' revelada")
    return jsonify({"ok": True, "password": password})


# ============================================================================
#  DIAGRAMA DE RED (Entrega 3) — generado a partir de padre_id de los equipos
# ============================================================================

@infra_bp.route("/sedes/<int:sede_id>/diagrama")
@login_required
@admin_requerido
def diagrama(sede_id):
    """Vista del diagrama interactivo de red para una sede."""
    sede = _sede_o_404(sede_id)
    equipos = sede.equipos.all()

    # Detectar equipos huérfanos (sin padre, excluyendo Internet/WAN que es la entrada normal)
    huerfanos = [e for e in equipos
                 if e.padre_id is None and e.tipo != "internet"]

    return render_template(
        "infraestructura/diagrama.html",
        sede=sede,
        cliente=sede.cliente,
        total_equipos=len(equipos),
        huerfanos=huerfanos,
    )


@infra_bp.route("/sedes/<int:sede_id>/diagrama/datos.json")
@login_required
@admin_requerido
def diagrama_datos(sede_id):
    """
    Endpoint AJAX que devuelve los nodos y aristas del diagrama en formato
    compatible con vis-network.
    """
    sede = _sede_o_404(sede_id)
    equipos = sede.equipos.all()

    # Colores por tipo (mismos colores que las cards en infraestructura)
    colores_tipo = {
        "internet": "#0ea5e9",
        "firewall": "#dc2626",
        "router": "#8b5cf6",
        "switch": "#f59e0b",
        "ap": "#10b981",
        "servidor": "#1f2937",
        "nas": "#7c3aed",
        "pc": "#3b82f6",
        "portatil": "#6366f1",
        "impresora": "#ec4899",
        "camara_ip": "#ef4444",
        "telefono_ip": "#06b6d4",
        "ups": "#84cc16",
        "otro": "#64748b",
    }

    # Iconos Unicode/emoji por tipo (vis-network usa emoji/símbolos en labels)
    # Para íconos reales usaremos imágenes SVG inline en una versión posterior
    # Por ahora, etiquetas con código corto
    nodos = []
    for eq in equipos:
        color = colores_tipo.get(eq.tipo, "#64748b")
        # Label compuesto: nombre + IP (si tiene)
        label_parts = [eq.nombre]
        if eq.ip:
            label_parts.append(eq.ip)
        label = "\n".join(label_parts)

        # Tooltip: HTML con datos completos del equipo (vis-network lo respeta)
        tooltip_lines = [f"<b>{eq.nombre}</b>", f"Tipo: {eq.tipo_label}"]
        if eq.marca or eq.modelo:
            tooltip_lines.append(f"Marca/modelo: {eq.marca or ''} {eq.modelo or ''}".strip())
        if eq.ip:
            tooltip_lines.append(f"IP: {eq.ip}")
        if eq.mac:
            tooltip_lines.append(f"MAC: {eq.mac}")
        if eq.ubicacion_fisica:
            tooltip_lines.append(f"Ubicación: {eq.ubicacion_fisica}")
        tooltip = "<br>".join(tooltip_lines)

        nodos.append({
            "id": eq.id,
            "label": label,
            "title": tooltip,
            "color": {
                "background": color,
                "border": color,
                "highlight": {"background": "#fff", "border": color},
            },
            "font": {"color": "white", "size": 13, "face": "Century Gothic, sans-serif"},
            "shape": "box",
            "borderWidth": 2,
            "margin": 10,
            "tipo": eq.tipo,           # para filtros en JS
            "tipo_label": eq.tipo_label,
            "icono": eq.tipo_icono,    # clase Bootstrap Icons
            "url_editar": url_for("infraestructura.equipo_editar",
                                  sede_id=sede.id, equipo_id=eq.id),
        })

    # Aristas: cada equipo con padre_id crea una conexión padre → hijo
    aristas = []
    for eq in equipos:
        if eq.padre_id:
            aristas.append({
                "from": eq.padre_id,
                "to": eq.id,
                "arrows": "to",
                "color": {"color": "#94a3b8", "highlight": "#635bff"},
                "smooth": {"type": "cubicBezier", "forceDirection": "vertical"},
                "width": 2,
            })

    return jsonify({
        "nodos": nodos,
        "aristas": aristas,
        "sede": {"id": sede.id, "nombre": sede.nombre, "cliente": sede.cliente.nombre},
    })
