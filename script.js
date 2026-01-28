document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Efecto Scroll Suave para los enlaces del menú
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
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
    const navContainer = document.querySelector('.nav-container');
    const navLinks = document.querySelector('.nav-links');
    
    if (navContainer && navLinks) {
        // Crear botón hamburguesa
        const toggleButton = document.createElement('button');
        toggleButton.innerHTML = '<i class="fa-solid fa-bars"></i>';
        toggleButton.className = 'mobile-menu-btn';
        toggleButton.style.display = 'none'; 
        toggleButton.style.background = 'none';
        toggleButton.style.border = 'none';
        toggleButton.style.fontSize = '1.5rem';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.color = '#333';
        
        navContainer.insertBefore(toggleButton, navLinks);

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
        checkMobile();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    
    // --- LÓGICA DE LA NUBE DE ETIQUETAS AUTOMÁTICA ---
    
    function generateWordCloud() {
        const container = document.getElementById('auto-tag-cloud');
        if (!container) return;

        // 1. Obtener solo los títulos de las secciones
        const targetSections = ['#posts', '#proyectos', '#charlas', '#publicaciones'];
        let text = "";
        targetSections.forEach(id => {
            const section = document.querySelector(id);
            if (section) {
                // Solo extraer títulos (.pub-title, h3, strong en títulos)
                const titles = section.querySelectorAll('.pub-title, h3, .card strong, .publication-item strong, li strong');
                titles.forEach(title => {
                    text += title.innerText + " ";
                });
            }
        });
        
        // 2. Limpieza de texto
        text = text.toLowerCase()
            .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "")
            .replace(/\s{2,}/g, " ");

        const words = text.split(" ");

        // 3. Lista de "Stop Words" (Palabras a ignorar en Español e Inglés)
        const stopWords = new Set([
            // Español
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", 
            "y", "o", "en", "a", "por", "para", "con", "sin", "sobre", "entre", "tras",
            "que", "qué", "como", "cómo", "donde", "cuando", "quien", "mas", "más",
            "mi", "tu", "su", "mis", "sus", "yo", "tu", "el", "ella", "nosotros",
            "soy", "eres", "es", "somos", "son", "estoy", "estas", "esta", "estamos", 
            "tengo", "tienes", "tiene", "hacer", "hace", "ver", "leer", "ir",
            "pero", "aunque", "sino", "porque", "pues", "01", "02", "03", "04", "05", "06", "07", "08",
            "pdf", "demo", "repo", "code", "aquí", "contact", "contacto", "Jesús", "paso",
            "mí", "soy", "sobre", "García", "modernas", "enfoque", "->", "predimedplus",
            
            // Inglés
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", 
            "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto", 
            "to", "with", "within", "without", "about", "above", "across", "after",
            "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her",
            "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "this", "that", "these", "those", "click", "here", "read", "more", "join",
            "new", "free", "learn", "between", "within", "without", "using", "used", "use",
            "also", "based", "data", "using", "using", "used", "use", "analysis", "results",
        ]);

        // 4. Contar Frecuencias
        const wordCounts = {};
        words.forEach(word => {
            if (!stopWords.has(word) && word.length > 2 && isNaN(word)) {
                wordCounts[word] = (wordCounts[word] || 0) + 1;
            }
        });

        // 5. Ordenar por frecuencia
        let sortedWords = Object.keys(wordCounts).map(word => {
            return { word: word, count: wordCounts[word] };
        });
        
        sortedWords.sort((a, b) => b.count - a.count);

        // top 30 palabras
        const topWords = sortedWords.slice(0, 30);
        if (topWords.length === 0) return;
        const maxCount = topWords[0].count;

        // 6. Función para mezclar (Shuffle)
        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }        
        shuffleArray(topWords);

        // 7. Generar el HTML
        container.innerHTML = '';
        
        topWords.forEach(item => {
            const link = document.createElement('a');
            link.textContent = item.word;
            link.className = 'tag';             
            link.href = `?tag=${item.word}`; 
            
            const ratio = item.count / maxCount;
            if (ratio > 0.8) link.classList.add('tag-xl');
            else if (ratio > 0.6) link.classList.add('tag-lg');
            else if (ratio > 0.4) link.classList.add('tag-md');
            else link.classList.add('tag-sm');
            
            link.title = `Ver entradas con: ${item.word}`;
            
            container.appendChild(link);
        });
    }

    // Ejecutar la función
    generateWordCloud();
});

// --- FUNCIONALIDAD DE FILTRADO POR TAG Y "VER MÁS PUBLICACIONES" ---
window.addEventListener('load', () => {
    
    // 1. FILTRADO POR TAG
    function filterContentByTag() {
        const urlParams = new URLSearchParams(window.location.search);
        const tag = urlParams.get('tag');

        if (tag) {
            const items = document.querySelectorAll('.card, .publication-item');
            
            items.forEach(item => {
                if (!item.textContent.toLowerCase().includes(tag)) {
                    item.style.display = 'none';
                }
            });

            setTimeout(() => {
                const mainContent = document.querySelector('main');
                if (mainContent) {
                    mainContent.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
        }
    }
    
    // 2. VER MÁS PUBLICACIONES
    setTimeout(() => {
        const publicacionesContainer = document.getElementById('publicaciones-content');
        const verMasBtn = document.getElementById('ver-mas-publicaciones');
        
        console.log('Container encontrado:', publicacionesContainer);
        console.log('Botón encontrado:', verMasBtn);
        
        if (publicacionesContainer && verMasBtn) {
            const publicaciones = publicacionesContainer.querySelectorAll('.card');
            const maxVisible = 5;
            
            console.log('Total de publicaciones encontradas:', publicaciones.length);
            
            // Ocultar publicaciones después de las primeras 5
            if (publicaciones.length > maxVisible) {
                publicaciones.forEach((pub, index) => {
                    if (index >= maxVisible) {
                        pub.classList.add('hidden-publication');
                        pub.style.display = 'none';
                        pub.style.visibility = 'hidden';
                    }
                });
                console.log('Se ocultaron', publicaciones.length - maxVisible, 'publicaciones');
            } else {
                // Si hay 5 o menos publicaciones, ocultar el botón
                verMasBtn.style.display = 'none';
                console.log('Hay 5 o menos publicaciones, botón ocultado');
            }
            
            // Evento click para mostrar todas las publicaciones
            verMasBtn.addEventListener('click', () => {
                console.log('Clic en ver más');
                const hiddenPubs = publicacionesContainer.querySelectorAll('.hidden-publication');
                
                hiddenPubs.forEach(pub => {
                    pub.style.display = 'block';
                    pub.style.visibility = 'visible';
                    pub.classList.remove('hidden-publication');
                });
                
                // Ocultar el botón después de mostrar todas
                verMasBtn.style.display = 'none';
                
                // Scroll suave hacia las publicaciones recién mostradas
                if (hiddenPubs.length > 0) {
                    hiddenPubs[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        } else {
            console.error('No se encontró el contenedor o el botón');
        }
    }, 100);
    
    // Ejecutar el filtro por tag
    filterContentByTag();
});
