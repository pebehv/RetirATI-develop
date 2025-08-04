# FunATI - Django Web Application

## Descripción
FunATI es una aplicación web social construida con Django que permite a los usuarios interactuar a través de publicaciones, chats, y más.

## Configuración y Ejecución

### Prerrequisitos
- Python 3.8 o superior
- Django 5.2.3

### Instalación

1. **Clonar el repositorio** (si aplica):
   ```bash
   git clone <repository-url>
   cd RetirATI
   ```

2. **Crear un entorno virtual**:
   ```bash
   python -m venv venv
   
   # En Windows:
   venv\Scripts\activate
   
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**:
   ```bash
   cd funATI
   python manage.py migrate
   ```

5. **Ejecutar el servidor de desarrollo**:
   ```bash
   python manage.py runserver
   ```

6. **Acceder a la aplicación**:
   - Abrir el navegador y ir a: `http://127.0.0.1:8000/`

## Estructura de URLs

### Páginas Principales:
- `/` - Página de inicio (landing page)
- `/login/` - Iniciar sesión
- `/register/` - Registrarse
- `/recover-password/` - Recuperar contraseña

### Páginas de la Aplicación:
- `/app/` - Página principal (muro)
- `/notifications/` - Notificaciones
- `/chats/` - Chats
- `/friends/` - Amigos
- `/settings/` - Configuración
- `/profile/` - Perfil del usuario
- `/edit-profile/` - Editar perfil
- `/followers/` - Seguidores
- `/follows/` - Seguidos
- `/publication/` - Vista de publicación

## Estructura de Archivos

```
funATI/
├── funATI/                 # Configuración principal del proyecto
│   ├── settings.py         # Configuración de Django
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuración WSGI
├── funATIAPP/             # Aplicación principal
│   ├── templates/         # Templates HTML
│   │   ├── base.html      # Template base principal
│   │   ├── auth_base.html # Template base para autenticación
│   │   └── *.html         # Páginas específicas
│   ├── static/            # Archivos estáticos
│   │   ├── css/           # Archivos CSS
│   │   ├── js/            # Archivos JavaScript
│   │   └── assets/        # Imágenes y otros recursos
│   ├── views.py           # Vistas de la aplicación
│   ├── urls.py            # URLs de la aplicación
│   └── models.py          # Modelos de datos
├── manage.py              # Script de administración de Django
└── requirements.txt       # Dependencias del proyecto
```

## Características

### Templates Base
- **`base.html`**: Template principal con sidebar y estructura completa
- **`auth_base.html`**: Template para páginas de autenticación

### Funcionalidades Implementadas
- ✅ Sistema de rutas completo
- ✅ Templates con herencia
- ✅ Archivos estáticos configurados
- ✅ Navegación entre páginas
- ✅ Formularios de autenticación
- ✅ Estructura responsive

### Páginas Disponibles
- **Página de Inicio**: Landing page con información de la aplicación
- **Autenticación**: Login, registro y recuperación de contraseña
- **Perfil**: Vista y edición del perfil del usuario
- **Social**: Seguidores, seguidos y amigos
- **Comunicación**: Chats y notificaciones
- **Configuración**: Ajustes de la aplicación

## Desarrollo

### Agregar Nuevas Páginas

1. **Crear la vista en `views.py`**:
   ```python
   def mi_nueva_pagina(request):
       return render(request, 'mi-pagina.html')
   ```

2. **Agregar la URL en `urls.py`**:
   ```python
   path('mi-pagina/', views.mi_nueva_pagina, name='mi_pagina'),
   ```

3. **Crear el template**:
   ```html
   {% extends 'base.html' %}
   {% block title %}Mi Página{% endblock %}
   {% block content %}
   <!-- Contenido aquí -->
   {% endblock %}
   ```

### Estructura de CSS
Los archivos CSS están organizados por funcionalidad:
- `styles.css` - Estilos generales
- `login.css` - Estilos de autenticación
- `chats.css` - Estilos de chats
- `notifications.css` - Estilos de notificaciones
- Y más...

## Notas Técnicas

- **Django Version**: 5.2.3
- **Template Engine**: Django Template Language
- **Static Files**: Configurados en `STATICFILES_DIRS`
- **Database**: SQLite (por defecto)
- **Development Server**: Puerto 8000

## Próximos Pasos

1. Implementar autenticación real
2. Agregar modelos de base de datos
3. Implementar funcionalidad de publicaciones
4. Agregar sistema de usuarios
5. Implementar chat en tiempo real

## Contribución

Para contribuir al proyecto:
1. Fork el repositorio
2. Crear una rama para tu feature
3. Hacer commit de los cambios
4. Crear un Pull Request

---

¡Disfruta desarrollando con FunATI! 🚀 