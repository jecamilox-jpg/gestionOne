/* ============================================================
   Layout Designer - Configuración GrapesJS
   ============================================================ */

(function () {
  "use strict";

  if (typeof grapesjs === "undefined") {
    console.error("GrapesJS no se cargó.");
    return;
  }

  const cfg = window.G1_LAYOUT || {};
  if (!cfg.id) return;

  const editor = grapesjs.init({
    container: "#gjs",
    height: "100%",
    width: "auto",
    storageManager: false,
    blockManager: {
      appendTo: "#blocks-panel",
      blocks: [
        {
          id: "logo",
          label: "Logo",
          category: "Elementos",
          content: `<div style="padding:10px"><img src="https://via.placeholder.com/120x40?text=LOGO" alt="Logo" style="max-width:160px"></div>`,
        },
        {
          id: "texto",
          label: "Texto",
          category: "Elementos",
          content: '<div style="padding:8px">Haz clic para editar este texto</div>',
        },
        {
          id: "titulo",
          label: "Título",
          category: "Elementos",
          content: '<h2 style="margin:0;padding:8px">Título</h2>',
        },
        {
          id: "tabla",
          label: "Tabla",
          category: "Elementos",
          content: `
            <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
              <thead>
                <tr style="background:#f5f5f5">
                  <th style="border:1px solid #ddd;padding:8px;text-align:left">Descripción</th>
                  <th style="border:1px solid #ddd;padding:8px;text-align:right">Cantidad</th>
                  <th style="border:1px solid #ddd;padding:8px;text-align:right">Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="border:1px solid #ddd;padding:8px">Producto 1</td>
                  <td style="border:1px solid #ddd;padding:8px;text-align:right">1</td>
                  <td style="border:1px solid #ddd;padding:8px;text-align:right">$ 0,00</td>
                </tr>
              </tbody>
            </table>`,
        },
        {
          id: "firma",
          label: "Firma",
          category: "Elementos",
          content: `
            <div style="margin-top:60px;padding:8px;text-align:center;font-family:sans-serif">
              <div style="border-top:1px solid #333;width:240px;margin:0 auto;padding-top:6px">
                Firma autorizada
              </div>
            </div>`,
        },
        {
          id: "imagen",
          label: "Imagen",
          category: "Elementos",
          content: { type: "image" },
        },
        {
          id: "qr",
          label: "Código QR",
          category: "Elementos",
          content: `<div style="padding:8px"><img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=GestionOne" alt="QR"></div>`,
        },
        {
          id: "separador",
          label: "Separador",
          category: "Elementos",
          content: '<hr style="border:none;border-top:1px solid #ccc;margin:12px 0">',
        },
        {
          id: "campo-numero",
          label: "Nº Documento",
          category: "Variables",
          content: '<span style="font-weight:600">{{numero}}</span>',
        },
        {
          id: "campo-fecha",
          label: "Fecha",
          category: "Variables",
          content: "<span>{{fecha}}</span>",
        },
        {
          id: "campo-cliente",
          label: "Cliente",
          category: "Variables",
          content: "<span>{{cliente_nombre}}</span>",
        },
        {
          id: "campo-nit",
          label: "NIT Cliente",
          category: "Variables",
          content: "<span>{{cliente_nit}}</span>",
        },
        {
          id: "campo-total",
          label: "Total",
          category: "Variables",
          content: '<span style="font-weight:600">$ {{total}}</span>',
        },
        {
          id: "campo-empresa",
          label: "Nombre empresa",
          category: "Variables",
          content: "<span>{{empresa_nombre}}</span>",
        },
      ],
    },
    panels: { defaults: [] },
    layerManager: { appendTo: "#layers-panel" },
    styleManager: { appendTo: "#styles-panel" },
    deviceManager: {
      devices: [
        { name: "A4", width: "794px" },
        { name: "Tablet", width: "768px" },
        { name: "Móvil", width: "375px" },
      ],
    },
    canvas: {
      styles: [],
    },
  });

  // Cargar contenido previo
  if (cfg.html) editor.setComponents(cfg.html);
  if (cfg.css) editor.setStyle(cfg.css);

  // Botón guardar
  const btnGuardar = document.getElementById("btn-guardar-layout");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", async () => {
      const payload = {
        html: editor.getHtml(),
        css: editor.getCss(),
        components: JSON.stringify(editor.getComponents()),
        styles: JSON.stringify(editor.getStyle()),
      };
      btnGuardar.disabled = true;
      btnGuardar.innerHTML = '<i class="bi bi-hourglass"></i> Guardando...';
      try {
        const resp = await fetch(cfg.saveUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (data.ok) {
          btnGuardar.innerHTML = '<i class="bi bi-check-lg"></i> Guardado';
          setTimeout(() => {
            btnGuardar.innerHTML = '<i class="bi bi-save"></i> Guardar';
            btnGuardar.disabled = false;
          }, 1500);
        } else {
          throw new Error(data.mensaje || "Error al guardar");
        }
      } catch (e) {
        alert("Error: " + e.message);
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = '<i class="bi bi-save"></i> Guardar';
      }
    });
  }

  window.G1Editor = editor;
})();
