"""
CRUD de Productos.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import Producto
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("productos", __name__, template_folder="../../templates/productos")


def _query_base():
    return Producto.query.filter_by(empresa_id=current_user.empresa_id)


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
                Producto.nombre.ilike(like),
                Producto.codigo.ilike(like),
                Producto.descripcion.ilike(like),
            )
        )
    if estado:
        query = query.filter_by(estado=estado)

    paginacion = query.order_by(Producto.nombre).paginate(
        page=pagina, per_page=15, error_out=False
    )

    if request.headers.get("HX-Request"):
        return render_template(
            "productos/_tabla.html", paginacion=paginacion, busqueda=busqueda
        )

    return render_template(
        "productos/lista.html",
        paginacion=paginacion,
        busqueda=busqueda,
        estado=estado,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nuevo():
    if request.method == "POST":
        producto = Producto(
            codigo=request.form["codigo"].strip(),
            nombre=request.form["nombre"].strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            precio=float(request.form.get("precio") or 0),
            iva=float(request.form.get("iva") or 19),
            estado=request.form.get("estado", "activo"),
            empresa_id=current_user.empresa_id,
        )
        db.session.add(producto)
        db.session.commit()
        registrar_evento("crear", "productos", f"Producto: {producto.codigo}")
        flash("Producto creado correctamente.", "success")
        return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", producto=None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    producto = _query_base().filter_by(id=id).first_or_404()
    if request.method == "POST":
        producto.codigo = request.form["codigo"].strip()
        producto.nombre = request.form["nombre"].strip()
        producto.descripcion = request.form.get("descripcion", "").strip()
        producto.precio = float(request.form.get("precio") or 0)
        producto.iva = float(request.form.get("iva") or 19)
        producto.estado = request.form.get("estado", "activo")
        db.session.commit()
        registrar_evento("editar", "productos", f"Producto: {producto.codigo}")
        flash("Producto actualizado.", "success")
        return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", producto=producto)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    producto = _query_base().filter_by(id=id).first_or_404()
    codigo = producto.codigo
    db.session.delete(producto)
    db.session.commit()
    registrar_evento("eliminar", "productos", f"Producto eliminado: {codigo}")
    flash("Producto eliminado.", "success")
    return redirect(url_for("productos.lista"))


@bp.route("/api/buscar")
@login_required
def api_buscar():
    """Endpoint JSON usado al construir cotizaciones."""
    q = request.args.get("q", "").strip()
    query = _query_base().filter_by(estado="activo")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Producto.nombre.ilike(like), Producto.codigo.ilike(like)))
    productos = query.limit(15).all()
    return jsonify([
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "precio": p.precio,
            "iva": p.iva,
        }
        for p in productos
    ])
