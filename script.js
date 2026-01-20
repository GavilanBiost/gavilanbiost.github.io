document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Efecto Scroll Suave para los enlaces del menú
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // Compensación de 70px por la barra de navegación fija
                const headerOffset = 70;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.scrollY - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth"
                });
            }
        });
    });

    // 2. Lógica del Menú Móvil (Hamburguesa)
    // Crearemos el botón dinámicamente si no existe para no romper tu HTML
    const navContainer = document.querySelector('.nav-container');
    const navLinks = document.querySelector('.nav-links');
    
    if (navContainer && navLinks) {
        // Crear botón hamburguesa
        const toggleButton = document.createElement('button');
        toggleButton.innerHTML = '<i class="fa-solid fa-bars"></i>';
        toggleButton.className = 'mobile-menu-btn';
        toggleButton.style.display = 'none'; // Se oculta por defecto en CSS, lo manejamos ahí
        
        // Estilos básicos para el botón (inyectados por JS para no tocar tu CSS)
        toggleButton.style.background = 'none';
        toggleButton.style.border = 'none';
        toggleButton.style.fontSize = '1.5rem';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.color = '#333';
        
        // Insertar botón antes de los enlaces
        navContainer.insertBefore(toggleButton, navLinks);

        // Funcionalidad Click
        toggleButton.addEventListener('click', () => {
            if (navLinks.style.display === 'flex') {
                navLinks.style.display = 'none';
            } else {
                navLinks.style.display = 'flex';
                navLinks.style.flexDirection = 'column';
                navLinks.style.position = 'absolute';
                navLinks.style.top = '60px';
                navLinks.style.left = '0';
                navLinks.style.width = '100%';
                navLinks.style.background = 'white';
                navLinks.style.padding = '20px';
                navLinks.style.boxShadow = '0 5px 10px rgba(0,0,0,0.1)';
            }
        });

        // Mostrar botón solo en móvil (Media Query en JS)
        const checkMobile = () => {
            if (window.innerWidth <= 768) {
                toggleButton.style.display = 'block';
                if(navLinks.style.position !== 'absolute') navLinks.style.display = 'none'; 
            } else {
                toggleButton.style.display = 'none';
                navLinks.style.display = 'flex';
                navLinks.style.position = 'static';
                navLinks.style.flexDirection = 'row';
                navLinks.style.boxShadow = 'none';
                navLinks.style.padding = '0';
            }
        };

        window.addEventListener('resize', checkMobile);
        checkMobile(); // Ejecutar al inicio
    }
});