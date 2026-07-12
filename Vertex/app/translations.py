TRANSLATIONS = {
    "es": {
        "nav.servicios": "Servicios",
        "nav.portafolio": "Portafolio",
        "nav.nosotros": "Nosotros",
        "nav.proceso": "Proceso",
        "nav.contacto": "Contacto",
        "nav.cta": "Cotiza tu proyecto",

        "footer.desc": "Desarrollo web profesional con Python, Flask, HTML, CSS y JavaScript.",
        "footer.servicios_title": "Servicios",
        "footer.servicio.landing": "Landing Page",
        "footer.servicio.frontend": "Diseño Frontend",
        "footer.servicio.backend": "Desarrollo Backend",
        "footer.servicio.fullstack": "Sitio Completo",
        "footer.servicio.blogcms": "Blog / CMS",
        "footer.empresa_title": "Empresa",
        "footer.contacto_title": "Contáctanos",
        "footer.github": "GitHub",
        "footer.copyright": "© 2026 AS Vertex · Todos los derechos reservados",
        "footer.privacidad": "Aviso de Privacidad",
        "footer.terminos": "Términos y Condiciones",
    },
    "en": {
        "nav.servicios": "Services",
        "nav.portafolio": "Portfolio",
        "nav.nosotros": "About",
        "nav.proceso": "Process",
        "nav.contacto": "Contact",
        "nav.cta": "Get a quote",

        "footer.desc": "Professional web development with Python, Flask, HTML, CSS and JavaScript.",
        "footer.servicios_title": "Services",
        "footer.servicio.landing": "Landing Page",
        "footer.servicio.frontend": "Frontend Design",
        "footer.servicio.backend": "Backend Development",
        "footer.servicio.fullstack": "Full Website",
        "footer.servicio.blogcms": "Blog / CMS",
        "footer.empresa_title": "Company",
        "footer.contacto_title": "Contact Us",
        "footer.github": "GitHub",
        "footer.copyright": "© 2026 AS Vertex · All rights reserved",
        "footer.privacidad": "Privacy Notice",
        "footer.terminos": "Terms & Conditions",
    },
}

def t(key):
    from flask import session
    lang = session.get("lang", "es")
    return TRANSLATIONS.get(lang, TRANSLATIONS["es"]).get(key, key)