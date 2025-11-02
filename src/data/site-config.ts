export type Image = {
    src: string;
    alt?: string;
    caption?: string;
};

export type Link = {
    text: string;
    href: string;
};

export type Hero = {
    title?: string;
    text?: string;
    image?: Image;
    actions?: Link[];
};

export type Subscribe = {
    title?: string;
    text?: string;
    formUrl: string;
};

export type SiteConfig = {
    website: string;
    logo?: Image;
    title: string;
    subtitle?: string;
    description: string;
    image?: Image;
    headerNavLinks?: Link[];
    footerNavLinks?: Link[];
    socialLinks?: Link[];
    hero?: Hero;
    subscribe?: Subscribe;
    postsPerPage?: number;
    projectsPerPage?: number;
};

const siteConfig: SiteConfig = {
    website: 'https://example.com',
    title: 'Jesús F García Gavilán',
    subtitle: 'Si hay un patrón, lo encontraré 🔍',
    description: 'A personal blog and portfolio site built with Astro.js and Tailwind CSS.',
    image: {
        src: '/dante-preview.jpg',
        alt: 'Dante - Astro.js and Tailwind CSS theme'
    },
    headerNavLinks: [
        {
            text: 'Home',
            href: '/'
        },
        {
            text: 'Proyectos',
            href: '/projects'
        },
        {
            text: 'Blog',
            href: '/blog'
        }
    ],
    footerNavLinks: [
        {
            text: 'Sobre mi',
            href: '/about'
        },
        {
            text: 'Contacto',
            href: '/contact'
        },
        {
            text: 'Términos',
            href: '/terms'
        }
    ],
    socialLinks: [
        {
            text: 'LinkdIn',
            href: 'https://www.linkedin.com/in/jesus-garcia-gavilan'
        },
        {
            text: 'GitHub',
            href: 'https://github.com/GavilanBiost'
        }
    ],
    hero: {
        title: 'Bienvenido a mi espacio personal',
        text: `👋 ¡Hola! Soy Jesús y soy bioestadístico.
        
        Desde 2018 he trabajado en el mundo de los datos aplicados a la salud y la investigación científica, cuando los análisis epidemiológicos eran la referencia y las herramientas bioinformáticas apenas comenzaban a abrirse paso. A lo largo de mi trayectoria, he participado en proyectos con todo tipo de datos como:
        - Socio-culturales
        - Nutricionales
        - Clínicos
        - Genéticos
        - Metabolómicos
        - Proteómicos
        - Metagenómicos
        Estoy especializado en el uso de R para el análisis estadístico y visualización, aunque también trabajo con Python y SQL, adaptándome siempre a las necesidades del proyecto y los datos que lo respaldan.
        
        📊 ¿Cuál es mi objetivo?
        Compartir herramientas, código y proyectos que reflejen mi experiencia en el análisis de datos complejos y la investigación bioestadística. Mi propósito es contribuir un poquito al conocimiento general y facilitar el acceso a recursos que ayuden a otros profesionales, futuros profesionales y estudiantes a resolver problemas reales a través de los datos.

        🧬 Áreas de interés:
        - Bioestadística avanzada
        - Análisis de datos multi-ómicos
        - Epidemiología
        - Visualización de datos complejos
        - Ciencia de datos aplicada a la salud
        Este espacio es mi manera de aprender, desarrollar y devolver a la comunidad parte de lo aprendido y de seguir creciendo junto a profesionales con intereses afines.`,
        image: {
            src: '/hero.jpeg',
            alt: 'A person sitting at a desk in front of a computer'
        },
        actions: [
            {
                text: 'Contactar',
                href: '/contact'
            }
        ]
    },
    subscribe: {
        title: 'Subscribe to Dante Newsletter',
        text: 'One update per week. All the latest posts directly in your inbox.',
        formUrl: '#'
    },
    postsPerPage: 8,
    projectsPerPage: 8
};

export default siteConfig;
