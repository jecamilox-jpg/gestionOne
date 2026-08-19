"""
Dashboard principal con métricas y gráficas.
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app import db
from app.models import Cliente, Producto, Cotizacion, CuentaCobro

bp = Blueprint("dashboard", __name__, template_folder="../../templates/dashboard")


@bp.route("/")
@login_required
def index():
    """Vista principal del dashboard."""
    empresa_id = current_user.empresa_id

    # KPIs
    total_clientes = Cliente.query.filter_by(empresa_id=empresa_id).count()
    total_productos = Producto.query.filter_by(empresa_id=empresa_id).count()

    inicio_mes = datetime.utcnow().replace(day=1).date()
    cotizaciones_mes = (
        Cotizacion.query.filter(
            Cotizacion.empresa_id == empresa_id,
            Cotizacion.fecha >= inicio_mes,
        ).count()
    )
    cuentas_pendientes = CuentaCobro.query.filter_by(
        empresa_id=empresa_id, estado="pendiente"
    ).count()

    valor_pendiente = (
        db.session.query(func.coalesce(func.sum(CuentaCobro.valor), 0))
        .filter(CuentaCobro.empresa_id == empresa_id, CuentaCobro.estado == "pendiente")
        .scalar()
    )
    valor_pagado_mes = (
        db.session.query(func.coalesce(func.sum(CuentaCobro.valor), 0))
        .filter(
            CuentaCobro.empresa_id == empresa_id,
            CuentaCobro.estado == "pagada",
            CuentaCobro.fecha >= inicio_mes,
        )
        .scalar()
    )

    # Ventas por mes (últimos 6 meses)
    hoy = datetime.utcnow().date()
    etiquetas, montos = [], []
    nombres_mes = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]
    for i in range(5, -1, -1):
        anio = hoy.year
        mes = hoy.month - i
        while mes <= 0:
            mes += 12
            anio -= 1
        inicio = datetime(anio, mes, 1).date()
        if mes == 12:
            fin = datetime(anio + 1, 1, 1).date()
        else:
            fin = datetime(anio, mes + 1, 1).date()
        total = (
            db.session.query(func.coalesce(func.sum(CuentaCobro.valor), 0))
            .filter(
                CuentaCobro.empresa_id == empresa_id,
                CuentaCobro.fecha >= inicio,
                CuentaCobro.fecha < fin,
                CuentaCobro.estado != "anulada",
            )
            .scalar()
        )
        etiquetas.append(f"{nombres_mes[mes - 1]} {anio}")
        montos.append(float(total or 0))

    # Estado de cartera
    estados = (
        db.session.query(CuentaCobro.estado, func.count(CuentaCobro.id))
        .filter(CuentaCobro.empresa_id == empresa_id)
        .group_by(CuentaCobro.estado)
        .all()
    )
    estados_dict = {e[0]: e[1] for e in estados}

    # Últimas cotizaciones
    ultimas_cotizaciones = (
        Cotizacion.query.filter_by(empresa_id=empresa_id)
        .order_by(Cotizacion.creada_en.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        total_clientes=total_clientes,
        total_productos=total_productos,
        cotizaciones_mes=cotizaciones_mes,
        cuentas_pendientes=cuentas_pendientes,
        valor_pendiente=valor_pendiente or 0,
        valor_pagado_mes=valor_pagado_mes or 0,
        etiquetas_meses=etiquetas,
        montos_meses=montos,
        estados_cartera=estados_dict,
        ultimas_cotizaciones=ultimas_cotizaciones,
    )
