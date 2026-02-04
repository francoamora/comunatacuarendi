// static/core/js/main.js (v3.7 - TACUARENDÍ FIX)
// - NO inyecta lightbox (porque ya lo tenés en el template)
// - No rompe si algún elemento no existe
// - Mantiene: preloader, menú móvil, navbar scroll, reveal animations

document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  // ==========================================
  // 0) PRELOADER
  // ==========================================
  const preloader = document.getElementById("preloader");
  if (preloader) {
    const hide = () => {
      preloader.style.opacity = "0";
      setTimeout(() => {
        preloader.style.display = "none";
      }, 500);
    };

    window.addEventListener("load", hide);
    setTimeout(hide, 3500); // fallback
  }

  // ==========================================
  // 1) MENÚ MÓVIL
  // ==========================================
  const menuBtn = document.querySelector(".mobile-menu-btn");
  const navMenu = document.querySelector(".nav-links");

  if (menuBtn && navMenu) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      navMenu.classList.toggle("active");

      const i = menuBtn.querySelector("i");
      if (!i) return;

      if (navMenu.classList.contains("active")) {
        i.classList.remove("fa-bars");
        i.classList.add("fa-xmark");
      } else {
        i.classList.remove("fa-xmark");
        i.classList.add("fa-bars");
      }
    });

    document.querySelectorAll(".nav-links a").forEach((link) => {
      link.addEventListener("click", () => {
        navMenu.classList.remove("active");
        const i = menuBtn.querySelector("i");
        if (!i) return;
        i.classList.remove("fa-xmark");
        i.classList.add("fa-bars");
      });
    });

    document.addEventListener("click", (e) => {
      if (!navMenu.classList.contains("active")) return;
      if (navMenu.contains(e.target) || menuBtn.contains(e.target)) return;

      navMenu.classList.remove("active");
      const i = menuBtn.querySelector("i");
      if (!i) return;
      i.classList.remove("fa-xmark");
      i.classList.add("fa-bars");
    });
  }

  // ==========================================
  // 2) NAVBAR SCROLL
  // ==========================================
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 20) navbar.classList.add("scrolled");
      else navbar.classList.remove("scrolled");
    });
  }

  // ==========================================
  // 3) REVEAL ANIMATIONS
  // ==========================================
  const revealElements = document.querySelectorAll(".reveal");
  if (revealElements.length) {
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("active");
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.1 }
    );

    revealElements.forEach((el) => io.observe(el));
  }

  // ==========================================
  // 4) (IMPORTANTE) LIGHTBOX
  // ==========================================
  // No tocamos el lightbox acá.
  // Lo maneja el script inline del template (openGalleryLightbox / openLightbox).

  console.log("⚡ TACUARENDÍ UI main.js v3.8: OK");
});
