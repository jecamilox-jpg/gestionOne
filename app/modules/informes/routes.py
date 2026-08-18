"""
Informes de estado por empresa — resumen ejecutivo con métricas clave.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import func, and_

from app import db
from app.models import (
    Cliente, Producto, Cotizacion, CuentaCobro,
    TrabajoFijo, ItemPresupuesto,
)

bp = Blueprint("informes", __name__, template_folder="../../templates/informes")

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


@bp.route("/")
@login_required
def index():
    """Informe de estado general de la empresa."""
    eid = current_user.empresa_id
    hoy = date.today()
    mes_actual = hoy.strftime("%Y-%m")
    mes_nombre = MESES_ES.get(hoy.month, "")

    # --- Clientes ---
    total_clientes = Cliente.query.filter_by(empresa_id=eid).count()
    clientes_activos = Cliente.query.filter_by(empresa_id=eid, estado="activo").count()

    # --- Productos ---
    total_productos = Producto.query.filter_by(empresa_id=eid).count()
    productos_activos = Producto.query.filter_by(empresa_id=eid, estado="activo").count()

    # --- Cotizaciones ---
    cotizaciones_total = Cotizacion.query.filter_by(empresa_id=eid).count()
    cotizaciones_mes = Cotizacion.query.filter(
        Cotizacion.empresa_id == eid,
        func.extract("month", Cotizacion.fecha) == hoy.month,
        func.extract("year", Cotizacion.fecha) == hoy.year,
    ).count()
    cotizaciones_valor_mes = db.session.query(
        func.coalesce(func.sum(Cotizacion.total), 0)
    ).filter(
        Cotizacion.empresa_id == eid,
        func.extract("month", Cotizacion.fecha) == hoy.month,
        func.extract("year", Cotizacion.fecha) == hoy.year,
    ).scalar() or 0

    # --- Cuentas de cobro ---
    cuentas_total = CuentaCobro.query.filter_by(empresa_id=eid).count()
    cuentas_pendientes = CuentaCobro.query.filter_by(empresa_id=eid, estado="pendiente").count()
    cuentas_pagadas = CuentaCobro.query.filter_by(empresa_id=eid, estado="pagada").count()

    valor_pendiente = db.session.query(
        func.coalesce(func.sum(CuentaCobro.valor), 0)
    ).filter_by(empresa_id=eid, estado="pendiente").scalar() or 0

    valor_pagado = db.session.query(
        func.coalesce(func.sum(CuentaCobro.valor), 0)
    ).filter_by(empresa_id=eid, estado="pagada").scalar() or 0

    valor_pagado_mes = db.session.query(
        func.coalesce(func.sum(CuentaCobro.valor), 0)
    ).filter(
        CuentaCobro.empresa_id == eid,
        CuentaCobro.estado == "pagada",
        func.extract("month", CuentaCobro.fecha) == hoy.month,
        func.extract("year", CuentaCobro.fecha) == hoy.year,
    ).scalar() or 0

    # --- Top 5 clientes por valor facturado ---
    top_clientes = (
        db.session.query(
            Cliente.nombre,
            func.count(CuentaCobro.id).label("num_cuentas"),
            func.coalesce(func.sum(CuentaCobro.valor), 0).label("total_valor"),
        )
        .join(CuentaCobro, CuentaCobro.cliente_id == Cliente.id)
        .filter(CuentaCobro.empresa_id == eid)
        .group_by(Cliente.id, Cliente.nombre)
        .order_by(func.sum(CuentaCobro.valor).desc())
        .limit(5)
        .all()
    )

    # --- Trabajo fijo ---
    trabajo_activo = (
        TrabajoFijo.query
        .filter_by(empresa_id=eid, estado="activo")
        .order_by(TrabajoFijo.id.desc())
        .first()
    )

    # --- Presupuesto del mes ---
    items_ppto = ItemPresupuesto.query.filter_by(empresa_id=eid, mes=mes_actual).all()
    ppto_total = sum(i.costo for i in items_ppto)
    ppto_q1 = sum(i.valor_q1 for i in items_ppto)
    ppto_q2 = sum(i.valor_q2 for i in items_ppto)
    ppto_pagados_q1 = sum(i.valor_q1 for i in items_ppto if getattr(i, "estado_q1", "") == "pago")
    ppto_pagados_q2 = sum(i.valor_q2 for i in items_ppto if getattr(i, "estado_q2", "") == "pago")

    return render_template(
        "informes/index.html",
        hoy=hoy, mes_nombre=mes_nombre,
        total_clientes=total_clientes, clientes_activos=clientes_activos,
        total_productos=total_productos, productos_activos=productos_activos,
        cotizaciones_total=cotizaciones_total, cotizaciones_mes=cotizaciones_mes,
        cotizaciones_valor_mes=cotizaciones_valor_mes,
        cuentas_total=cuentas_total, cuentas_pendientes=cuentas_pendientes,
        cuentas_pagadas=cuentas_pagadas,
        valor_pendiente=valor_pendiente, valor_pagado=valor_pagado,
        valor_pagado_mes=valor_pagado_mes,
        top_clientes=top_clientes,
        trabajo_activo=trabajo_activo,
        ppto_total=ppto_total, ppto_q1=ppto_q1, ppto_q2=ppto_q2,
        ppto_pagados_q1=ppto_pagados_q1, ppto_pagados_q2=ppto_pagados_q2,
        items_ppto=items_ppto,
    )
