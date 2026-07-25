/* ============================================================
   Editor de cotizaciones: filas dinámicas + cálculo de totales
   ============================================================ */

(function () {
  "use strict";

  const tbody = document.getElementById("detalle-tbody");
  const btnAdd = document.getElementById("btn-add-detalle");
  const inputSubtotal = document.getElementById("display-subtotal");
  const inputIva = document.getElementById("display-iva");
  const inputTotal = document.getElementById("display-total");

  if (!tbody) return;

  function fmt(n) {
    return (parseFloat(n) || 0).toFixed(2);
  }

  function recalcular() {
    let sub = 0, iva = 0;
    tbody.querySelectorAll("tr").forEach((tr) => {
      const cantidad = parseFloat(tr.querySelector(".d-cantidad").value) || 0;
      const precio = parseFloat(tr.querySelector(".d-precio").value) || 0;
      const ivaPct = parseFloat(tr.querySelector(".d-iva").value) || 0;
      const subF = cantidad * precio;
      const ivaF = subF * (ivaPct / 100);
      tr.querySelector(".d-total").textContent = G1.formatMoney(subF + ivaF);
      sub += subF;
      iva += ivaF;
    });
    if (inputSubtotal) inputSubtotal.textContent = G1.formatMoney(sub);
    if (inputIva) inputIva.textContent = G1.formatMoney(iva);
    if (inputTotal) inputTotal.textContent = G1.formatMoney(sub + iva);
  }

  function nuevaFila(detalle) {
    detalle = detalle || {};
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <select class="form-select form-select-sm d-producto">
          <option value="">-- Personalizado --</option>
        </select>
      </td>
      <td>
        <input type="text" name="descripcion[]" class="form-control form-control-sm d-descripcion"
               value="${detalle.descripcion || ""}" placeholder="Descripción">
        <input type="hidden" name="producto_id[]" class="d-producto-id" value="${detalle.producto_id || ""}">
      </td>
      <td style="width: 90px">
        <input type="number" min="0" step="0.01" name="cantidad[]" class="form-control form-control-sm d-cantidad"
               value="${detalle.cantidad || 1}">
      </td>
      <td style="width: 130px">
        <input type="number" min="0" step="0.01" name="valor_unitario[]" class="form-control form-control-sm d-precio"
               value="${detalle.valor_unitario || 0}">
      </td>
      <td style="width: 80px">
        <input type="number" min="0" step="0.01" name="iva[]" class="form-control form-control-sm d-iva"
               value="${detalle.iva || 19}">
      </td>
      <td class="d-total fw-medium" style="width: 130px">$ 0,00</td>
      <td style="width: 40px">
        <button type="button" class="btn btn-sm btn-icon btn-outline-secondary d-quitar" title="Eliminar">
          <i class="bi bi-x"></i>
        </button>
      </td>`;

    // Llenar select de productos
    const sel = tr.querySelector(".d-producto");
    (window.GESTION_PRODUCTOS || []).forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.dataset.precio = p.precio;
      opt.dataset.iva = p.iva;
      opt.dataset.nombre = p.nombre;
      opt.textContent = `${p.codigo} — ${p.nombre}`;
      sel.appendChild(opt);
    });

    if (detalle.producto_id) sel.value = detalle.producto_id;

    // Cambio de producto -> rellena valores
    sel.addEventListener("change", () => {
      const opt = sel.options[sel.selectedIndex];
      if (opt.value) {
        tr.querySelector(".d-descripcion").value = opt.dataset.nombre;
        tr.querySelector(".d-precio").value = opt.dataset.precio;
        tr.querySelector(".d-iva").value = opt.dataset.iva;
        tr.querySelector(".d-producto-id").value = opt.value;
      } else {
        tr.querySelector(".d-producto-id").value = "";
      }
      recalcular();
    });

    // Cambios en inputs
    tr.querySelectorAll(".d-cantidad, .d-precio, .d-iva").forEach((el) =>
      el.addEventListener("input", recalcular)
    );

    // Eliminar fila
    tr.querySelector(".d-quitar").addEventListener("click", () => {
      tr.remove();
      recalcular();
    });

    tbody.appendChild(tr);
    recalcular();
  }

  if (btnAdd) {
    btnAdd.addEventListener("click", () => nuevaFila());
  }

  // Cargar detalles existentes o crear primera fila
  const detallesIniciales = window.GESTION_DETALLES_INICIALES || [];
  if (detallesIniciales.length) {
    detallesIniciales.forEach((d) => nuevaFila(d));
  } else {
    nuevaFila();
  }

  // Exponer recálculo
  window.G1Cotizacion = { recalcular, nuevaFila };
})();
