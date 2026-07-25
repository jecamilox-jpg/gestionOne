/* ============================================================
   GestiónOne - JavaScript principal
   ============================================================ */

(function () {
  "use strict";

  // ---------- Sidebar colapsable (desktop + mobile) ----------
  const sidebar = document.querySelector(".g1-sidebar");
  const toggleBtn = document.querySelector("#g1-sidebar-toggle");
  const isMobile = () => window.innerWidth <= 768;

  // Create backdrop for mobile overlay
  let backdrop = document.querySelector(".g1-sidebar-backdrop");
  if (!backdrop && sidebar) {
    backdrop = document.createElement("div");
    backdrop.className = "g1-sidebar-backdrop";
    sidebar.parentNode.insertBefore(backdrop, sidebar.nextSibling);
  }

  function closeMobileSidebar() {
    if (sidebar) {
      sidebar.classList.remove("mobile-open");
      if (backdrop) backdrop.classList.remove("show");
      document.body.style.overflow = "";
    }
  }

  if (sidebar && toggleBtn) {
    // Restaurar estado guardado (solo desktop)
    if (!isMobile() && localStorage.getItem("g1.sidebar.collapsed") === "1") {
      sidebar.classList.add("collapsed");
    }

    toggleBtn.addEventListener("click", () => {
      if (isMobile()) {
        const opening = !sidebar.classList.contains("mobile-open");
        sidebar.classList.toggle("mobile-open");
        if (backdrop) backdrop.classList.toggle("show");
        document.body.style.overflow = opening ? "hidden" : "";
      } else {
        sidebar.classList.toggle("collapsed");
        sidebar.classList.toggle("expanded");
        localStorage.setItem(
          "g1.sidebar.collapsed",
          sidebar.classList.contains("collapsed") ? "1" : "0"
        );
      }
    });

    // Close on backdrop tap
    if (backdrop) {
      backdrop.addEventListener("click", closeMobileSidebar);
    }

    // Close sidebar when clicking a nav link (mobile)
    sidebar.querySelectorAll(".g1-nav-link").forEach((link) => {
      link.addEventListener("click", () => {
        if (isMobile()) closeMobileSidebar();
      });
    });

    // Handle resize: clean up mobile state when going to desktop
    window.addEventListener("resize", () => {
      if (!isMobile()) {
        closeMobileSidebar();
        sidebar.classList.remove("mobile-open");
      }
    });
  }

  // ---------- Auto-dismiss de alertas ----------
  document.querySelectorAll(".g1-flash-stack .alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s, transform 0.4s";
      alert.style.opacity = "0";
      alert.style.transform = "translateX(20px)";
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // ---------- Confirmación para formularios destructivos ----------
  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const mensaje = form.dataset.confirm || "¿Estás seguro?";
      if (!confirm(mensaje)) {
        e.preventDefault();
      }
    });
  });

  // ---------- Helpers globales ----------
  window.G1 = window.G1 || {};

  window.G1.formatMoney = function (n) {
    const num = parseFloat(n) || 0;
    return (
      "$ " +
      num
        .toFixed(2)
        .replace(".", ",")
        .replace(/\B(?=(\d{3})+(?!\d))/g, ".")
    );
  };

  // Auto-focus en primer input de formularios
  const firstInput = document.querySelector("form input:not([type=hidden]):not([readonly]):not([disabled])");
  if (firstInput && !document.body.classList.contains("no-autofocus")) {
    // No autoenfocar en móvil, donde despliega teclado de inmediato
    if (window.innerWidth > 768) {
      try { firstInput.focus(); } catch (_) {}
    }
  }
})();
