"""Resume template metadata registry — matches reactive-resume template names."""

_TEMPLATES = [
    {
        "id": "azurill",
        "name": "Azurill",
        "thumbnail_url": "/static/templates/azurill.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "bronzor",
        "name": "Bronzor",
        "thumbnail_url": "/static/templates/bronzor.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "chikorita",
        "name": "Chikorita",
        "thumbnail_url": "/static/templates/chikorita.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "ditgar",
        "name": "Ditgar",
        "thumbnail_url": "/static/templates/ditgar.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "ditto",
        "name": "Ditto",
        "thumbnail_url": "/static/templates/ditto.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "gengar",
        "name": "Gengar",
        "thumbnail_url": "/static/templates/gengar.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "glalie",
        "name": "Glalie",
        "thumbnail_url": "/static/templates/glalie.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "kakuna",
        "name": "Kakuna",
        "thumbnail_url": "/static/templates/kakuna.jpg",
        "page_limit": 1,
        "supported_sections": ["Experience", "Education", "Skills", "Projects"],
    },
    {
        "id": "lapras",
        "name": "Lapras",
        "thumbnail_url": "/static/templates/lapras.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "leafish",
        "name": "Leafish",
        "thumbnail_url": "/static/templates/leafish.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "meowth",
        "name": "Meowth",
        "thumbnail_url": "/static/templates/meowth.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "onyx",
        "name": "Onyx",
        "thumbnail_url": "/static/templates/onyx.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications", "Achievements"],
    },
    {
        "id": "pikachu",
        "name": "Pikachu",
        "thumbnail_url": "/static/templates/pikachu.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "rhyhorn",
        "name": "Rhyhorn",
        "thumbnail_url": "/static/templates/rhyhorn.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "scizor",
        "name": "Scizor",
        "thumbnail_url": "/static/templates/scizor.jpg",
        "page_limit": 2,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Certifications"],
    },
    {
        "id": "jake",
        "name": "Jake",
        "thumbnail_url": "/static/templates/jake.jpg",
        "page_limit": 1,
        "supported_sections": ["Experience", "Education", "Skills", "Projects", "Technical Skills"],
    },
]


def list_templates():
    return list(_TEMPLATES)


def get_template(template_id: str) -> dict | None:
    return next((t for t in _TEMPLATES if t["id"] == template_id), None)
