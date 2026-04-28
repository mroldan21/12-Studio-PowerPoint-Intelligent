# PPTX Studio — Intelligent Edition

> Generador inteligente de presentaciones PowerPoint con IA vía OpenRouter

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![FastAPI](https://img.shields.io/badge/fastapi-0.109+-orange)

## 🚀 Características

- **Generación con IA**: Crea presentaciones completas desde texto usando modelos LLM gratuitos
- **Múltiples tipos de entrada**: Resúmenes, apuntes extensos, investigaciones, edición de PPTX
- **Tema visual profesional**: Tema oscuro "PitchSync" con colores neon
- **API REST**: Endpoints para integración con otras aplicaciones
- **Interfaz web SPA**: Frontend moderno con vista previa en tiempo real

## 📋 Requisitos

- Python 3.10+
- API Key de [OpenRouter](https://openrouter.ai/) (gratuito)

## 🔧 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd tu_directorio
```

### 2. Crear entorno con Conda (recomendado)

```bash
# Crear entorno con Python 3.10+
conda create -n pptx_studio python=3.10 -y

# Activar entorno
conda activate pptx_studio

# Opcional: agregar al proyecto
conda env export > environment.yml
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variable de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
OPENROUTER_API_KEY=tu_api_key_aqui
```

O exporta directamente:

```bash
# Windows
set OPENROUTER_API_KEY=tu_api_key

# Linux/Mac
export OPENROUTER_API_KEY=tu_api_key
```

### 5. Obtener API Key

1. Ve a [OpenRouter.ai](https://openrouter.ai/)
2. Crea una cuenta gratuita
3. Genera tu API Key desde el dashboard

## 🎯 Uso

### Iniciar el servidor

#### Opción 1: Con Uvicorn (recomendado para desarrollo)
```bash
uvicorn main:app --reload
```

#### Opción 2: Con Python directo
```bash
python main.py
```

El servidor arrancará en: `http://localhost:8000`

> **Nota**: La opción `--reload` permite que el servidor se reinicie automáticamente cuando detecte cambios en el código.

### Acceso a la interfaz

- **Frontend**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Interfaz web |
| `GET` | `/health` | Estado del servicio |
| `GET` | `/models` | Listar modelos disponibles |
| `POST` | `/generate` | Generar presentación |
| `POST` | `/generate/json` | Obtener estructura JSON |

### Ejemplo de generación con curl

```bash
curl -X POST "http://localhost:8000/generate" \
  -F "prompt=Presentación sobre inteligencia artificial en medicina" \
  -F "input_type=summary" \
  -F "filename=ia_medicina.pptx" \
  -o ia_medicina.pptx
```

## 💻 Interfaz Web

### Pestañas de entrada

1. **Resumen**: Para temas generales (8-10 diapositivas)
2. **Apunte**: Para apuntes extensos (12-15 diapositivas)
3. **Investigación**: Para proyectos de investigación
4. **Editar PPTX**: Mejora presentaciones existentes

### Opciones

- **Modelo**: Seleccionar modelo IA (Gemma 27B, Llama 70B, etc.)
- **Incluir imágenes IA**: Añadir placeholders para imágenes
- **Nombre de archivo**: Personalizar nombre de salida

## 📁 Estructura del Proyecto

```
pptx_studio/
├── config/
│   ├── models_config.json      # Configuración de modelos
│   └── themes/
│       └── pitchsync_dark.json # Tema visual
├── core/
│   ├── ai_client.py           # Cliente OpenRouter
│   ├── content_orchestrator.py # Orquestador de contenido
│   ├── pptx_engine.py         # Motor PPTX
│   └── slide_designer.py      # Diseñador visual
├── processors/
│   ├── ai_content_processor.py
│   ├── image_processor.py
│   ├── notes_processor.py
│   └── slide_design_processor.py
├── static/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── templates/
│   ├── blank.pptx
│   └── pitchsync_master.pptx
├── main.py                    # Entry point
└── requirements.txt
```

## 🔌 Modelos Disponibles

| Modelo | Context | Recomendado para |
|--------|---------|------------------|
| Gemma 3 27B | 131K | Resúmenes, apuntes extensos |
| Hermes 3 405B | 128K | Investigación profunda |
| Llama 3.3 70B | 128K | Notas rápidas |
| Gemma 3 12B | 128K | Tareas multimodales |
| Llama 3.2 3B | 128K | Procesamiento ligero |

## 🐛 Solución de Problemas

### "OPENROUTER_API_KEY no configurada"

```bash
# Verificar que la variable esté configurada
echo %OPENROUTER_API_KEY%  # Windows
echo $OPENROUTER_API_KEY   # Linux/Mac

# O verificar el entorno conda
conda env list
conda activate pptx_studio
```

### Error al generar presentación

1. Verifica que tienes crédito en OpenRouter (cuenta gratuita)
2. Revisa el log en la terminal
3. Prueba con otro modelo

### Puerto en uso

```bash
# Cambiar puerto
set PORT=8001
python main.py
```

## 📄 Licencia

MIT License - Ver archivo `LICENSE` para más detalles.

## 🤝 Contribuir

1. Fork del repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

---

⭐️ Si te gusta este proyecto, ¡considera darle una estrella!