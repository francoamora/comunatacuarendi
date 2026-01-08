// Esperar a que el documento cargue
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Efecto Sticky Header (Cambia sombra al hacer scroll)
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.style.boxShadow = "0 4px 20px rgba(0,0,0,0.15)";
        } else {
            header.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
        }
    });

    // 2. Smooth Scroll para navegadores antiguos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    console.log("Sitio de Tacuarendí cargado correctamente en modo experto.");
});