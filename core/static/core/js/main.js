// static/core/js/main.js (v4.3 - TACUARENDÍ UI UNIFICADO)
// ✅ Unifica: preloader, menú móvil, navbar scroll, reveal, lightbox, videos, filtros, sugerencias, trámites
// ✅ Evita solapamientos: NO hay scripts inline compitiendo
// ✅ Anti "abre-cierra": trámites abre con pointerdown en CAPTURE + bloqueo de click posterior
// ✅ Scroll-lock con contador (shared) para lightbox/sugerencias/trámites

(() => {
  "use strict";

  if (window.__TACUARENDI_MAIN_V43__) return;
  window.__TACUARENDI_MAIN_V43__ = true;

  const onReady = (fn) => {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn, { once: true });
  };

  // ----------------------------
  // Helpers
  // ----------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const prefersReducedMotion = (() => {
    try {
      return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch {
      return false;
    }
  })();

  const escapeHtml = (str) =>
    String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

  // ----------------------------
  // Scroll lock (contador shared)
  // ----------------------------
  const lockScroll = () => {
    const b = document.body;
    const n = (parseInt(b.dataset.lockCount || "0", 10) || 0) + 1;
    b.dataset.lockCount = String(n);
    if (n === 1) b.style.overflow = "hidden";
  };

  const unlockScroll = () => {
    const b = document.body;
    const n = Math.max((parseInt(b.dataset.lockCount || "0", 10) || 0) - 1, 0);
    b.dataset.lockCount = String(n);
    if (n === 0) b.style.overflow = "";
  };

  // Compat por si quedó algún onclick viejo en otro template
  window.__lockScroll = lockScroll;
  window.__unlockScroll = unlockScroll;

  // ----------------------------
  // Overlay manager (anti superposición)
  // ----------------------------
  const closeAllOverlays = (exceptEl = null) => {
    // Lightbox
    if (lightbox && lightbox !== exceptEl && lightbox.classList.contains("active")) closeLightbox(true);

    // Sugerencias
    if (sugModal && sugModal !== exceptEl && sugModal.classList.contains("open")) closeSugModal(true);

    // Videos
    if (videoModal && videoModal !== exceptEl && videoModal.classList.contains("active")) closeVideoModal(true);

    // Trámites
    if (tramiteModal && tramiteModal !== exceptEl && tramiteModal.classList.contains("active")) closeTramite(true);
  };

  // =========================================================
  // 0) PRELOADER
  // =========================================================
  const preloader = $("#preloader");

  const hidePreloader = () => {
    if (!preloader) return;
    preloader.style.opacity = "0";
    setTimeout(() => {
      preloader.style.display = "none";
    }, 450);
  };

  window.addEventListener("load", hidePreloader);
  setTimeout(hidePreloader, 3500); // fallback

  // =========================================================
  // 1) MENÚ MÓVIL (robusto)
  // =========================================================
  const menuBtn = $(".mobile-menu-btn");
  const navMenu = $(".nav-links");

  const setMenuOpen = (open) => {
    if (!menuBtn || !navMenu) return;
    navMenu.classList.toggle("active", !!open);
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");

    const i = menuBtn.querySelector("i");
    if (!i) return;

    if (open) {
      i.classList.remove("fa-bars");
      i.classList.add("fa-xmark");
    } else {
      i.classList.remove("fa-xmark");
      i.classList.add("fa-bars");
    }
  };

  if (menuBtn && navMenu) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      setMenuOpen(!navMenu.classList.contains("active"));
    });

    $$(".nav-links a").forEach((link) => {
      link.addEventListener("click", () => setMenuOpen(false));
    });

    document.addEventListener("click", (e) => {
      if (!navMenu.classList.contains("active")) return;
      if (navMenu.contains(e.target) || menuBtn.contains(e.target)) return;
      setMenuOpen(false);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (navMenu.classList.contains("active")) setMenuOpen(false);
    });
  }

  // =========================================================
  // 2) NAVBAR SCROLL (rAF throttle)
  // =========================================================
  const navbar = $(".navbar");
  if (navbar) {
    let ticking = false;

    const update = () => {
      if (window.scrollY > 20) navbar.classList.add("scrolled");
      else navbar.classList.remove("scrolled");
      ticking = false;
    };

    window.addEventListener(
      "scroll",
      () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(update);
      },
      { passive: true }
    );

    update();
  }

  // =========================================================
  // 3) REVEAL ANIMATIONS
  // =========================================================
  const revealElements = $$(".reveal");
  if (revealElements.length) {
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      revealElements.forEach((el) => el.classList.add("active"));
    } else {
      const io = new IntersectionObserver(
        (entries, obs) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            entry.target.classList.add("active");
            obs.unobserve(entry.target);
          }
        },
        { threshold: 0.1 }
      );
      revealElements.forEach((el) => io.observe(el));
    }
  }

  // =========================================================
  // 4) LIGHTBOX (único)
  // =========================================================
  const lightbox = $("#lightbox");
  const lightboxImg = $("#lightbox-img");

  let lbImages = [];
  let lbIndex = 0;
  let lbLastFocused = null;

  const readImagesFrom = (trigger) => {
    const raw = trigger?.getAttribute?.("data-images");
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      return (parsed || []).filter(Boolean);
    } catch {
      const img = trigger.querySelector?.("img");
      return img?.src ? [img.src] : [];
    }
  };

  const updateLightbox = () => {
    if (!lightboxImg || !lbImages.length) return;
    if (prefersReducedMotion) {
      lightboxImg.src = lbImages[lbIndex];
      return;
    }
    lightboxImg.style.opacity = "0";
    setTimeout(() => {
      lightboxImg.src = lbImages[lbIndex];
      lightboxImg.style.opacity = "1";
    }, 120);
  };

  const openLightbox = (images, opener) => {
    if (!lightbox) return;
    const clean = (images || []).filter(Boolean);
    if (!clean.length) return;

    closeAllOverlays(lightbox);

    lbImages = clean;
    lbIndex = 0;
    lbLastFocused = opener || document.activeElement;

    updateLightbox();

    lightbox.classList.add("active");
    lightbox.setAttribute("aria-hidden", "false");
    lockScroll();

    // arrows hidden if single image
    const prevBtn = $('[data-lightbox-prev]', lightbox);
    const nextBtn = $('[data-lightbox-next]', lightbox);
    const multi = lbImages.length > 1;
    if (prevBtn) prevBtn.style.display = multi ? "" : "none";
    if (nextBtn) nextBtn.style.display = multi ? "" : "none";

    const closeBtn = $('[data-lightbox-close]', lightbox);
    if (closeBtn) closeBtn.focus({ preventScroll: true });
  };

  const closeLightbox = (silent = false) => {
    if (!lightbox || !lightbox.classList.contains("active")) return;
    lightbox.classList.remove("active");
    lightbox.setAttribute("aria-hidden", "true");
    unlockScroll();

    if (!silent && lbLastFocused && typeof lbLastFocused.focus === "function") {
      lbLastFocused.focus({ preventScroll: true });
    }
    lbLastFocused = null;
    lbImages = [];
    lbIndex = 0;
  };

  const changeLightbox = (dir) => {
    if (!lbImages.length) return;
    lbIndex += dir;
    if (lbIndex >= lbImages.length) lbIndex = 0;
    if (lbIndex < 0) lbIndex = lbImages.length - 1;
    updateLightbox();
  };

  // Delegación: abrir desde cualquier [data-gallery="lightbox"]
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest('[data-gallery="lightbox"][data-images]');
    if (!trigger) return;

    // si es un link real dentro, no intervenimos
    if (e.target.closest("a")) return;

    e.preventDefault();
    openLightbox(readImagesFrom(trigger), trigger);
  });

  // Teclado: Enter / Space en cards
  document.addEventListener("keydown", (e) => {
    const trigger = e.target.closest?.('[data-gallery="lightbox"][data-images]');
    if (!trigger) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openLightbox(readImagesFrom(trigger), trigger);
    }
  });

  // Controles lightbox
  if (lightbox) {
    lightbox.addEventListener("click", (e) => {
      // click en fondo => cerrar
      if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", (e) => {
      if (!lightbox.classList.contains("active")) return;
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowRight") changeLightbox(1);
      if (e.key === "ArrowLeft") changeLightbox(-1);
    });

    const closeBtn = $('[data-lightbox-close]', lightbox);
    const prevBtn = $('[data-lightbox-prev]', lightbox);
    const nextBtn = $('[data-lightbox-next]', lightbox);

    if (closeBtn) closeBtn.addEventListener("click", () => closeLightbox());
    if (prevBtn) prevBtn.addEventListener("click", () => changeLightbox(-1));
    if (nextBtn) nextBtn.addEventListener("click", () => changeLightbox(1));
  }

  // =========================================================
  // 5) FILTROS OBRAS (sin onclick)
  // =========================================================
  const obrasSection = $("#obras");
  if (obrasSection) {
    obrasSection.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-obras-filter]");
      if (!btn) return;

      e.preventDefault();
      const cat = btn.getAttribute("data-obras-filter") || "all";

      $$(".filter-btn", obrasSection).forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      $$(".card-obra", obrasSection).forEach((card) => {
        const show = cat === "all" || card.dataset.category === cat;
        card.style.display = show ? "block" : "none";
        if (show && !prefersReducedMotion) {
          card.style.animation = "fadeIn 0.6s ease forwards";
        } else {
          card.style.animation = "";
        }
      });
    });
  }

  // =========================================================
  // 6) SUGERENCIAS (modal)
  // =========================================================
  const sugModal = $("#sugModal");
  let sugLastFocused = null;

  const openSugModal = (opener) => {
    if (!sugModal) return;

    closeAllOverlays(sugModal);

    sugLastFocused = opener || document.activeElement;
    sugModal.classList.add("open");
    sugModal.setAttribute("aria-hidden", "false");
    lockScroll();

    const focusable = sugModal.querySelector("select, textarea, input, button");
    if (focusable) focusable.focus({ preventScroll: true });
  };

  const closeSugModal = (silent = false) => {
    if (!sugModal || !sugModal.classList.contains("open")) return;
    sugModal.classList.remove("open");
    sugModal.setAttribute("aria-hidden", "true");
    unlockScroll();

    if (!silent && sugLastFocused && typeof sugLastFocused.focus === "function") {
      sugLastFocused.focus({ preventScroll: true });
    }
    sugLastFocused = null;
  };

  // abrir/cerrar por data attrs
  document.addEventListener("click", (e) => {
    const openBtn = e.target.closest('[data-modal-open="sugModal"]');
    if (openBtn) {
      e.preventDefault();
      openSugModal(openBtn);
      return;
    }

    const closeBtn = e.target.closest('[data-modal-close="sugModal"]');
    if (closeBtn) {
      e.preventDefault();
      closeSugModal();
      return;
    }
  });

  if (sugModal) {
    sugModal.addEventListener("click", (e) => {
      if (e.target === sugModal) closeSugModal();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (sugModal.classList.contains("open")) closeSugModal();
    });
  }

  // Compat global por si quedó un onclick en otro lado
  window.openSugModal = () => openSugModal(document.activeElement);
  window.closeSugModal = () => closeSugModal();

  // =========================================================
  // 7) VIDEOS (modal único)
  // =========================================================
  const videoModal = $("#videoModal");
  const videoFrame = $("#videoFrame");
  const videoFallback = $("#videoFallback");
  const videoDirect = $("#videoDirect");
  const videoTitle = $("#videoModalTitle");
  const videoCloseBtn = videoModal ? $("[data-video-close]", videoModal) : null;
  let videoLastFocused = null;

  const withAutoplay = (url) => {
    if (!url) return "";
    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}autoplay=1`;
  };

  const openVideoModal = (trigger) => {
    if (!videoModal || !trigger) return;

    const embedUrl = trigger.getAttribute("data-video-src") || "";
    const directUrl = trigger.getAttribute("data-video-url") || embedUrl;
    const title = trigger.getAttribute("data-video-title") || "Video";

    if (!embedUrl && !directUrl) return;

    closeAllOverlays(videoModal);

    videoLastFocused = trigger;
    if (videoTitle) videoTitle.textContent = title;

    if (embedUrl && videoFrame) {
      videoFrame.src = withAutoplay(embedUrl);
      videoFrame.title = title;
      videoFrame.hidden = false;
      if (videoFallback) videoFallback.hidden = true;
    } else {
      if (videoFrame) {
        videoFrame.src = "";
        videoFrame.hidden = true;
      }
      if (videoFallback) videoFallback.hidden = false;
    }

    if (videoDirect && directUrl) videoDirect.href = directUrl;

    videoModal.classList.add("active");
    videoModal.setAttribute("aria-hidden", "false");
    lockScroll();

    if (videoCloseBtn) videoCloseBtn.focus({ preventScroll: true });
  };

  const closeVideoModal = (silent = false) => {
    if (!videoModal || !videoModal.classList.contains("active")) return;

    videoModal.classList.remove("active");
    videoModal.setAttribute("aria-hidden", "true");
    if (videoFrame) videoFrame.src = "";
    unlockScroll();

    if (!silent && videoLastFocused && typeof videoLastFocused.focus === "function") {
      videoLastFocused.focus({ preventScroll: true });
    }
    videoLastFocused = null;
  };

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-video-open]");
    if (!trigger) return;
    e.preventDefault();
    openVideoModal(trigger);
  });

  document.addEventListener("keydown", (e) => {
    const trigger = e.target.closest?.("[data-video-open]");
    if (!trigger) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openVideoModal(trigger);
    }
  });

  if (videoModal) {
    if (videoCloseBtn) videoCloseBtn.addEventListener("click", () => closeVideoModal());

    videoModal.addEventListener("click", (e) => {
      if (e.target === videoModal) closeVideoModal();
    });

    const videoCard = $(".video-modal-card", videoModal);
    if (videoCard) videoCard.addEventListener("click", (e) => e.stopPropagation());

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && videoModal.classList.contains("active")) closeVideoModal();
    });
  }

  window.openVideoModal = openVideoModal;
  window.closeVideoModal = closeVideoModal;

  // =========================================================
  // 8) TRÁMITES (modal único + data) ANTI-ABRE/CIERRA
  // =========================================================
  const tramiteModal = $("#tramiteModal");
  const tramitesData = window.__TRAMITES_DATA__ || {};

  const tIcon = $("#tramiteModalIcon");
  const tTitle = $("#tramiteModalTitle");
  const tMeta = $("#tramiteModalMeta");
  const tReq = $("#tramiteModalReq");
  const tFooter = $("#tramiteModalFooter");
  const tPdf = $("#tramiteModalPdf");
  const tCloseBtn = tramiteModal ? $(".close-modal", tramiteModal) : null;

  let tLastFocused = null;

  const renderTramiteMeta = (t) => {
    const rows = [];
    if (t.responsable) rows.push(`<div class="info-row"><i class="fa-solid fa-user-tie"></i><div><strong>Responsable:</strong> ${escapeHtml(t.responsable)}</div></div>`);
    if (t.horario) rows.push(`<div class="info-row"><i class="fa-regular fa-clock"></i><div><strong>Horarios:</strong> ${escapeHtml(t.horario)}</div></div>`);
    if (t.telefono) rows.push(`<div class="info-row"><i class="fa-solid fa-phone"></i><div><strong>Contacto:</strong> ${escapeHtml(t.telefono)}</div></div>`);
    if (tMeta) tMeta.innerHTML = rows.join("") || `<div class="info-row"><i class="fa-solid fa-circle-info"></i><div>Información disponible en administración.</div></div>`;
  };

  const openTramite = (id, opener) => {
    if (!tramiteModal) return;
    const t = tramitesData[String(id)];
    if (!t) return;

    closeAllOverlays(tramiteModal);

    tLastFocused = opener || document.activeElement;

    if (tIcon) tIcon.className = (t.icono || "fa-solid fa-file");
    if (tTitle) tTitle.textContent = t.nombre || "Trámite";

    renderTramiteMeta(t);
    if (tReq) tReq.innerHTML = t.requisitos_html || "Consultar en administración.";

    const hasPdf = !!(t.pdf_url && String(t.pdf_url).trim().length);
    if (tFooter) tFooter.hidden = !hasPdf;
    if (hasPdf && tPdf) tPdf.href = t.pdf_url;

    tramiteModal.classList.add("active");
    tramiteModal.setAttribute("aria-hidden", "false");
    lockScroll();

    if (tCloseBtn) tCloseBtn.focus({ preventScroll: true });
  };

  const closeTramite = (silent = false) => {
    if (!tramiteModal || !tramiteModal.classList.contains("active")) return;
    tramiteModal.classList.remove("active");
    tramiteModal.setAttribute("aria-hidden", "true");
    unlockScroll();

    if (!silent && tLastFocused && typeof tLastFocused.focus === "function") {
      tLastFocused.focus({ preventScroll: true });
    }
    tLastFocused = null;
  };

  // bind solo si existe data y modal
  const canUseTramites = !!(tramiteModal && tramitesData && Object.keys(tramitesData).length);

  if (canUseTramites) {
    // ABRIR: pointerdown en CAPTURE (anti "abre/cierra" por otros listeners)
    document.addEventListener("pointerdown", (e) => {
      const el = e.target.closest("#tramites [data-tramite-id]");
      if (!el) return;

      // si tocó un <a> real, no intervenimos
      if (e.target.closest("a")) return;

      e.preventDefault();
      e.stopPropagation();

      const id = el.getAttribute("data-tramite-id");
      requestAnimationFrame(() => openTramite(id, el));
    }, true);

    // BLOQUEO: click posterior (evita doble procesamiento)
    document.addEventListener("click", (e) => {
      const el = e.target.closest("#tramites [data-tramite-id]");
      if (!el) return;
      if (e.target.closest("a")) return;

      e.preventDefault();
      e.stopImmediatePropagation();
    }, true);

    // Teclado: Enter/Espacio
    document.addEventListener("keydown", (e) => {
      const el = e.target.closest?.("#tramites .card-tramite[data-tramite-id]");
      if (!el) return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        e.stopPropagation();
        const id = el.getAttribute("data-tramite-id");
        requestAnimationFrame(() => openTramite(id, el));
      }
    }, true);

    // Cerrar: X
    if (tCloseBtn) {
      tCloseBtn.addEventListener("click", (e) => {
        e.preventDefault();
        closeTramite();
      });
    }

    // Cerrar: overlay click
    tramiteModal.addEventListener("click", (e) => {
      if (e.target === tramiteModal) closeTramite();
    });

    // Evitar bubbling dentro de la card
    const tCard = $(".info-modal-card", tramiteModal);
    if (tCard) tCard.addEventListener("click", (e) => e.stopPropagation());

    // Cerrar: ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && tramiteModal.classList.contains("active")) closeTramite();
    });
  }

  // Compat global (si quedara algún onclick en otra vista)
  window.openTramite = openTramite;
  window.closeTramite = closeTramite;

  // =========================================================
  // Log
  // =========================================================
  console.log("⚡ TACUARENDÍ UI main.js v4.3: OK");
})();
