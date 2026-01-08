document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. MENÚ MÓVIL (HAMBURGUESA) ---
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navMenu = document.querySelector('.nav-links');
    const header = document.querySelector('.navbar');

    // Toggle del menú al hacer clic
    menuBtn.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        // Cambiar el ícono de hamburguesa a X (opcional si usas FontAwesome dinámico)
        const icon = menuBtn.querySelector('i');
        if (navMenu.classList.contains('active')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-xmark');
        } else {
            icon.classList.remove('fa-xmark');
            icon.classList.add('fa-bars');
        }
    });

    // Cerrar menú al hacer clic en un enlace (UX Pro)
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            const icon = menuBtn.querySelector('i');
            icon.classList.remove('fa-xmark');
            icon.classList.add('fa-bars');
        });
    });

    // --- 2. EFECTO STICKY NAVBAR (GLASSMORPHISM) ---
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    console.log("⚡ Sistema Tacuarendí v1.0: ONLINE");
});