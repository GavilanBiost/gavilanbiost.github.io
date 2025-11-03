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
    website: 'https://gavilanbiost.github.io',
    title: 'Jesús F García Gavilán',
    /*subtitle: 'Si hay un patrón, lo encontraré 🔍',*/
    description: 'A personal blog and portfolio site',
    image: {
        src: '',
        alt: ''
    },
    headerNavLinks: [
        {
            text: 'Home',
            href: '/'
        },
        {
            text: 'Proyectos',
            href: '/projects'
        }/*,
        {
            text: 'Blog',
            href: '/blog'
        }*/
    ],
    footerNavLinks: [
        /*{
            text: 'Sobre mi',
            href: '/about'
        },*/
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
            text: 'LinkedIn',
            href: 'https://www.linkedin.com/in/jesus-garcia-gavilan'
        },
        {
            text: 'GitHub',
            href: 'https://github.com/GavilanBiost'
        }
    ],
    hero: {
        title: 'Bienvenido a mi espacio personal',
        text: `👋 ¡Hola! Soy Jesús, bioestadístico y científico de datos especializado en el análisis e interpretación de datos aplicados a la salud e investigación científica.
        <p>Desde 2018 trabajo en el ámbito de la ciencia de datos en salud, una etapa en la que la estadística tradicional convivía con el auge de la bioinformática y el aprendizaje automático. Esta evolución me ha permitido integrar metodologías clásicas y modernas para extraer conocimiento útil a partir de datos complejos y heterogéneos. 
        </p><p>A lo largo de mi trayectoria, he participado en proyectos que abarcan múltiples tipos de datos: socioculturales, nutricionales, clínicos, genéticos, metabolómicos, proteómicos y metagenómicos. Mi especialidad es el uso de R para el análisis estadístico, modelado y visualización de datos, aunque también trabajo con Python y SQL, adaptando las herramientas a las necesidades de cada proyecto.
        </p><p> ¿Cuál es mi objetivo?
        </p><p>Compartir herramientas, código y proyectos que reflejen mi experiencia en bioestadística y en ciencia de datos aplicadas a la salud.
        </p><p>Busco contribuir al conocimiento colectivo y facilitar el acceso a recursos que ayuden a profesionales, investigadores y estudiantes a resolver problemas reales mediante el uso riguroso y creativo de los datos.
        </p><p> Este espacio es mi manera de aprender, experimentar y colaborar con una comunidad que cree, como yo, que los datos pueden impulsar avances significativos en la investigación, la salud y la toma de decisiones basada en evidencia.`,
        image: {
            src: '/e12ac28f-6872-4b76-9e8a-fe1fd5792af5.jpg',
            alt: 'Una foto mía en un congreso'
        },
        actions: [
            {
                text: 'Contactar',
                href: '/contact'
            }
        ]
    },
    subscribe: {
        title: 'Suscríbete a mi newsletter',
        text: 'Una actualización por semana. Todas las últimas publicaciones directamente en tu bandeja de entrada.',
        formUrl: '#'
    },
    postsPerPage: 8,
    projectsPerPage: 8
};

export default siteConfig;
