"""
CRUD de Clientes con búsqueda en tiempo real vía HTMX.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import Cliente
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("clientes", __name__, template_folder="../../templates/clientes")


def _query_base():
    return Cliente.query.filter_by(empresa_id=current_user.empresa_id)


@bp.route("/")
@login_required
def lista():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    pagina = int(request.args.get("pagina", 1))

    query = _query_base()
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            or_(
                Cliente.nombre.ilike(like),
                Cliente.nit.ilike(like),
                Cliente.correo.ilike(like),
                Cliente.ciudad.ilike(like),
            )
        )
    if estado:
        query = query.filter_by(estado=estado)

    paginacion = query.order_by(Cliente.nombre).paginate(
        page=pagina, per_page=15, error_out=False
    )

    # HTMX: solo el fragmento de tabla
    if request.headers.get("HX-Request"):
        return render_template(
            "clientes/_tabla.html", paginacion=paginacion, busqueda=busqueda
        )

    return render_template(
        "clientes/lista.html",
        paginacion=paginacion,
        busqueda=busqueda,
        estado=estado,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nuevo():
    if request.method == "POST":
        cliente = Cliente(
            nombre=request.form["nombre"].strip(),
            nit=request.form.get("nit", "").strip(),
            direccion=request.form.get("direccion", "").strip(),
            ciudad=request.form.get("ciudad", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            correo=request.form.get("correo", "").strip(),
            estado=request.form.get("estado", "activo"),
            empresa_id=current_user.empresa_id,
        )
        db.session.add(cliente)
        db.session.commit()
        registrar_evento("crear", "clientes", f"Cliente: {cliente.nombre}")
        flash("Cliente creado correctamente.", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("clientes/form.html", cliente=None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    cliente = _query_base().filter_by(id=id).first_or_404()
    if request.method == "POST":
        cliente.nombre = request.form["nombre"].strip()
        cliente.nit = request.form.get("nit", "").strip()
        cliente.direccion = request.form.get("direccion", "").strip()
        cliente.ciudad = request.form.get("ciudad", "").strip()
        cliente.telefono = request.form.get("telefono", "").strip()
        cliente.correo = request.form.get("correo", "").strip()
        cliente.estado = request.form.get("estado", "activo")
        db.session.commit()
        registrar_evento("editar", "clientes", f"Cliente: {cliente.nombre}")
        flash("Cliente actualizado.", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("clientes/form.html", cliente=cliente)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    cliente = _query_base().filter_by(id=id).first_or_404()
    nombre = cliente.nombre
    db.session.delete(cliente)
    db.session.commit()
    registrar_evento("eliminar", "clientes", f"Cliente eliminado: {nombre}")
    flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes.lista"))


@bp.route("/<int:id>")
@login_required
def detalle(id):
    cliente = _query_base().filter_by(id=id).first_or_404()
    return render_template("clientes/detalle.html", cliente=cliente)
