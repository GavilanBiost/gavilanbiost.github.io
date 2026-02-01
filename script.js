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
            "associated", "study", "studies", "based", "model", "models", "results", "conclusions",
            "trial",
            
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
            link.href = `?tag=${encodeURIComponent(item.word)}`; 
            
            const ratio = item.count / maxCount;
            if (ratio > 0.8) link.classList.add('tag-xl');
            else if (ratio > 0.6) link.classList.add('tag-lg');
            else if (ratio > 0.4) link.classList.add('tag-md');
            else link.classList.add('tag-sm');
            
            link.title = `Ver entradas con: ${item.word}`;
            
            // Asegurar que navegue correctamente
            link.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = `${window.location.pathname}?tag=${encodeURIComponent(item.word)}`;
            });
            
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
            // Crear banner de filtro
            const filterBanner = document.createElement('div');
            filterBanner.id = 'filter-banner';
            filterBanner.style.cssText = `
                position: fixed;
                top: 70px;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                text-align: center;
                z-index: 999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                font-size: 1rem;
            `;
            filterBanner.innerHTML = `
                <div style="max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1;">
                        <i class="fa-solid fa-filter" style="margin-right: 8px;"></i>
                        Mostrando artículos que contienen: <strong style="font-size: 1.1rem;">"${tag}"</strong>
                    </div>
                    <button id="clear-filter" style="
                        background: white;
                        color: #667eea;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <i class="fa-solid fa-times"></i> Limpiar filtro
                    </button>
                </div>
            `;
            document.body.insertBefore(filterBanner, document.body.firstChild);
            
            // Añadir evento al botón limpiar
            document.getElementById('clear-filter').addEventListener('click', () => {
                window.location.href = window.location.pathname;
            });
            
            // Ajustar el padding del body para compensar el banner
            document.querySelector('main').style.paddingTop = '100px';

            // Filtrar contenido
            const sections = ['#publicaciones', '#posts', '#proyectos', '#charlas'];
            let totalVisible = 0;
            let totalHidden = 0;
            
            sections.forEach(sectionId => {
                const section = document.querySelector(sectionId);
                if (section) {
                    const items = section.querySelectorAll('.card, .publication-item');
                    
                    items.forEach(item => {
                        const itemText = item.textContent.toLowerCase();
                        const tagLower = tag.toLowerCase();
                        
                        if (itemText.includes(tagLower)) {
                            item.style.display = '';
                            item.style.opacity = '1';
                            item.style.animation = 'fadeIn 0.5s ease-in';
                            // Añadir highlight visual
                            item.style.borderLeft = '4px solid #667eea';
                            item.style.backgroundColor = '#f8f9ff';
                            totalVisible++;
                        } else {
                            item.style.display = 'none';
                            totalHidden++;
                        }
                    });
                    
                    // Ocultar botón "ver más" cuando hay filtro activo
                    const verMasBtn = section.querySelector('[id^="ver-mas-"]');
                    if (verMasBtn) {
                        verMasBtn.style.display = 'none';
                    }
                }
            });
            
            // Mostrar contador de resultados
            if (totalVisible > 0) {
                const counter = document.createElement('div');
                counter.style.cssText = `
                    text-align: center;
                    margin: 20px 0;
                    font-size: 1.1rem;
                    color: #667eea;
                    font-weight: 600;
                `;
                counter.innerHTML = `<i class="fa-solid fa-check-circle"></i> Se encontraron ${totalVisible} resultado${totalVisible !== 1 ? 's' : ''}`;
                
                // Insertar después del banner
                const mainContent = document.querySelector('main');
                if (mainContent && mainContent.firstChild) {
                    mainContent.insertBefore(counter, mainContent.firstChild);
                }
            }
            
            // Añadir estilos para la animación
            if (!document.getElementById('filter-animation-styles')) {
                const style = document.createElement('style');
                style.id = 'filter-animation-styles';
                style.textContent = `
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(10px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
                document.head.appendChild(style);
            }

            // Scroll suave al contenido principal
            setTimeout(() => {
                const mainContent = document.querySelector('main');
                if (mainContent) {
                    mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
    }
    
    // 2. FUNCIÓN GENÉRICA PARA "VER MÁS"
    function setupVerMas(containerId, buttonId, maxVisible, itemName) {
        setTimeout(() => {
            const container = document.getElementById(containerId);
            const verMasBtn = document.getElementById(buttonId);
            
            console.log(`[${itemName}] Container encontrado:`, container);
            console.log(`[${itemName}] Botón encontrado:`, verMasBtn);
            
            if (container && verMasBtn) {
                const items = container.querySelectorAll('.card');
                
                console.log(`[${itemName}] Total de items encontrados:`, items.length);
                
                // Ocultar items después de los primeros maxVisible
                if (items.length > maxVisible) {
                    items.forEach((item, index) => {
                        if (index >= maxVisible) {
                            item.classList.add('hidden-item');
                            item.style.display = 'none';
                            item.style.visibility = 'hidden';
                        }
                    });
                    console.log(`[${itemName}] Se ocultaron`, items.length - maxVisible, 'items');
                } else {
                    // Si hay maxVisible o menos items, ocultar el botón
                    verMasBtn.style.display = 'none';
                    console.log(`[${itemName}] Hay ${maxVisible} o menos items, botón ocultado`);
                }
                
                // Evento click para mostrar todos los items
                verMasBtn.addEventListener('click', () => {
                    console.log(`[${itemName}] Clic en ver más`);
                    const hiddenItems = container.querySelectorAll('.hidden-item');
                    
                    hiddenItems.forEach(item => {
                        item.style.display = 'block';
                        item.style.visibility = 'visible';
                        item.classList.remove('hidden-item');
                    });
                    
                    // Ocultar el botón después de mostrar todas
                    verMasBtn.style.display = 'none';
                    
                    // Scroll suave hacia los items recién mostrados
                    if (hiddenItems.length > 0) {
                        hiddenItems[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            } else {
                console.error(`[${itemName}] No se encontró el contenedor o el botón`);
            }
        }, 100);
    }
    
    // Aplicar "Ver más" a las diferentes secciones
    setupVerMas('publicaciones-content', 'ver-mas-publicaciones', 5, 'Publicaciones');
    setupVerMas('posts-content', 'ver-mas-posts', 3, 'Posts');
    setupVerMas('proyectos', 'ver-mas-proyectos', 3, 'Proyectos');
    
    // Ejecutar el filtro por tag
    filterContentByTag();
});

// --- AVISO DE COOKIES ---
document.addEventListener('DOMContentLoaded', () => {
    const banner = document.getElementById('cookie-banner');
    const overlay = document.getElementById('cookie-overlay');
    const acceptBtn = document.getElementById('cookie-accept');
    const declineBtn = document.getElementById('cookie-decline');

    if (!banner || !overlay || !acceptBtn || !declineBtn) return;

    const GA_MEASUREMENT_ID = 'G-XXXXXXXXXX';
    const GTM_ID = 'GTM-IM5FCFZW';

    const loadGoogleAnalytics = () => {
        if (!GA_MEASUREMENT_ID || GA_MEASUREMENT_ID === 'G-XXXXXXXXXX') return;
        const gaScript = document.createElement('script');
        gaScript.async = true;
        gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
        document.head.appendChild(gaScript);

        window.dataLayer = window.dataLayer || [];
        function gtag(){window.dataLayer.push(arguments);} // eslint-disable-line no-inner-declarations
        gtag('js', new Date());
        gtag('config', GA_MEASUREMENT_ID, { anonymize_ip: true });
    };

    const loadGtm = () => {
        if (!GTM_ID) return;
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
        const gtmScript = document.createElement('script');
        gtmScript.async = true;
        gtmScript.src = `https://www.googletagmanager.com/gtm.js?id=${GTM_ID}`;
        document.head.appendChild(gtmScript);
    };

    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
        banner.style.display = 'block';
        overlay.style.display = 'block';
    }
    if (consent === 'accepted') {
        loadGoogleAnalytics();
        loadGtm();
    }

    const saveConsent = (value) => {
        localStorage.setItem('cookie_consent', value);
        banner.style.display = 'none';
        overlay.style.display = 'none';
    };

    acceptBtn.addEventListener('click', () => {
        saveConsent('accepted');
        loadGoogleAnalytics();
        loadGtm();
    });
    declineBtn.addEventListener('click', () => saveConsent('declined'));
});
