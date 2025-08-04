# 🚨 Guía de Arreglos Rápidos

## 🔧 **CORRECCIONES APLICADAS - Reconstruir Contenedor**

### ❗ **IMPORTANTE: DEBES RECONSTRUIR COMPLETAMENTE**

```bash
# 1. PARAR TODO
docker-compose down

# 2. LIMPIAR (OPCIONAL PERO RECOMENDADO)
docker system prune -f

# 3. RECONSTRUIR SIN CACHE
docker-compose build --no-cache

# 4. INICIAR
docker-compose up
```

## 🐛 **Errores Corregidos:**

### ✅ **1. Error de Zona Horaria (ZoneInfoNotFoundError)**
**Problema**: `No time zone found with key UTC`  
**Solución**: Instalado `tzdata` y configurado zona horaria Venezuela

### ✅ **2. Template JavaScript Error**  
**Problema**: Errores de sintaxis en test_chat.html  
**Solución**: Usado `json_script` filter para pasar datos a JavaScript

### ✅ **3. Middleware Complejo**  
**Problema**: Middleware personalizado causaba errores  
**Solución**: Simplificado a usar solo AuthMiddlewareStack estándar

### ✅ **4. Consumer Error Handling**  
**Problema**: Sin manejo robusto de errores  
**Solución**: Mejorado try-catch y validaciones

---

## 📋 **PASOS PARA VERIFICAR QUE FUNCIONA:**

### **1. Verificar Logs de Startup**
```bash
docker-compose logs web | grep -E "(✅|❌|Starting|Django setup)"
```

**Deberías ver**:
- ✅ Django setup successful
- ✅ Daphne started successfully (o Django runserver started)
- ✅ Apache server started

### **2. Verificar Servicios**
```bash
# Health check
docker-compose exec web /app/healthcheck.sh

# Debe mostrar:
# ✅ Redis is running
# ✅ Django server is running on port 8001  
# ✅ Apache proxy is running on port 80
```

### **3. Probar Aplicación**
```bash
# Abrir en navegador:
http://localhost:8000/login/

# Debe cargar la página de login SIN errores 500
```

### **4. Probar Chat (SI LA APP FUNCIONA)**
```bash
# Abrir en navegador:
http://localhost:8000/test-chat/test_room/

# Debe mostrar página de chat con estado "Connected" en verde
```

---

## 🚨 **SI AÚN NO FUNCIONA:**

### **Error 500 en cualquier página:**
```bash
# Ver logs detallados
docker-compose logs web | tail -50

# Buscar errores específicos
docker-compose logs web | grep -i "error\|exception\|traceback"
```

### **Daphne no inicia:**
```bash
# Verificar que Django funciona básicamente
docker-compose exec web python3 manage.py check

# Verificar configuración ASGI
docker-compose exec web python3 -c "from funATI.asgi import application; print('ASGI OK')"
```

### **Apache no proxy correctamente:**
```bash
# Verificar que Django responde directamente
curl http://localhost:8001/login/

# Verificar que Apache está corriendo
docker-compose exec web apache2ctl status
```

---

## 🆘 **SOLUCIÓN DE EMERGENCIA:**

Si nada funciona, usar modo simple sin WebSockets:

### **1. Desactivar Channels temporalmente:**
```python
# En funATI/settings.py, comentar:
# INSTALLED_APPS = [
#     'daphne',  # <-- Comentar esta línea
#     'channels', # <-- Comentar esta línea
# ]

# Y comentar:
# ASGI_APPLICATION = 'funATI.asgi.application'
# CHANNEL_LAYERS = {...}
```

### **2. Usar solo WSGI:**
```bash
# En start.sh, cambiar a:
python3 manage.py runserver 0.0.0.0:8001 &
```

### **3. Verificar que funcione:**
```bash
docker-compose up --build
# Debería funcionar todo excepto el chat en tiempo real
```

---

## 📞 **INFORMACIÓN DE DEBUG:**

### **Comandos útiles:**
```bash
# Ver todos los logs
docker-compose logs -f web

# Entrar al contenedor
docker-compose exec web bash

# Verificar Python y Django
docker-compose exec web python3 --version
docker-compose exec web python3 -c "import django; print(django.get_version())"

# Verificar base de datos
docker-compose exec web python3 manage.py dbshell

# Verificar usuarios existentes
docker-compose exec web python3 manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.all())"
```

### **Archivos importantes a revisar:**
- `/app/funATI/funATI/settings.py` - Configuración Django
- `/app/funATI/funATI/asgi.py` - Configuración ASGI
- `/etc/apache2/sites-available/funati.conf` - Configuración Apache

---

**🎯 Con estas correcciones, el sistema debería funcionar. Si persisten problemas, es probable que sea un problema de la aplicación Django original, no del contenedor.** 