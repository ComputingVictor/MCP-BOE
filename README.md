# MCP BOE 🇪🇸

**Model Context Protocol para el Boletín Oficial del Estado español**

<img width="512" height="512" alt="image" src="https://github.com/user-attachments/assets/cd1c5e79-add7-466c-bcbd-554b81a2fef9" />


Un servidor MCP que permite a Claude y otros LLMs acceder a la API oficial del BOE para consultar legislación consolidada, sumarios diarios y tablas auxiliares del gobierno español.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Características

- **🔍 Búsqueda de Legislación**: Buscar en más de 50,000 normas consolidadas
- **📰 Sumarios del BOE**: Acceder a publicaciones diarias del BOE y BORME  
- **🏛️ Tablas Auxiliares**: Consultar códigos de departamentos, materias y rangos normativos
- **⚡ API REST**: Interfaz HTTP para usar desde cualquier aplicación
- **🤖 Compatible con MCP**: Funciona con Claude Code, Ollama y otros clientes MCP
- **📊 Datos Oficiales**: Conecta directamente con la API oficial del BOE

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Configuración con Claude](#-configuración-con-claude)
- [API REST](#-api-rest)
- [Ejemplos](#-ejemplos)
- [Herramientas Disponibles](#-herramientas-disponibles)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## 🛠️ Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación rápida con uvx (Recomendado)

Si tienes [uvx](https://docs.astral.sh/uv/guides/tools/) instalado, puedes usar directamente el MCP servidor sin instalación manual:

```bash
# Verificar que uvx está instalado
uvx --version

# Ejecutar directamente desde el repositorio
uvx --from git+https://github.com/olivermontes/MCP-BOE.git mcp-boe --help
```

### Instalación desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/ComputingVictor/MCP-BOE.git
cd MCP-BOE

# Instalar solo las dependencias básicas
pip install -e .

# O instalar con API REST
pip install -e ".[api]"

# O instalar todo para desarrollo
pip install -e ".[dev]"
```

### Verificar instalación

```bash
# Prueba rápida de conectividad
python examples/basic_usage.py connectivity

# Prueba completa de funcionalidades
python examples/basic_usage.py quick
```

## ⚡ Uso Rápido

### Prueba de Conectividad

```bash
# Verificar que todo funciona
python examples/basic_usage.py connectivity
```

### Demo Interactivo

```bash
# Explorar funcionalidades de forma interactiva
python examples/basic_usage.py interactive
```

### Ejemplos Específicos

```bash
# Buscar legislación
python examples/basic_usage.py search

# Ver sumarios del BOE
python examples/basic_usage.py summary

# Consultar departamentos
python examples/basic_usage.py departments
```

## 🔧 Configuración con Claude

### Claude Code (Recomendado)

#### Opción 1: Con uvx (Recomendado para simplicidad)

**uvx** es una herramienta que simplifica enormemente la instalación y ejecución de paquetes Python. Con uvx no necesitas:
- Crear entornos virtuales manualmente
- Instalar dependencias
- Configurar variables de entorno como PYTHONPATH

uvx se encarga automáticamente de crear un entorno aislado y descargar todas las dependencias necesarias.

1. **Usar uvx directamente**:

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/olivermontes/MCP-BOE.git", "mcp-boe"]
    }
  }
}
```

También puedes usar el archivo de configuración de ejemplo incluido:
```bash
# Descargar y usar la configuración de ejemplo
curl -O https://raw.githubusercontent.com/olivermontes/MCP-BOE/main/claude_mcp_config_uvx.json
```

2. **Configurar en Claude Code**:
```bash
# Usar configuración personalizada
/config-mcp /ruta/a/tu/claude_mcp_config.json

# O usar configuración de ejemplo
/config-mcp claude_mcp_config_uvx.json
```

#### Opción 2: Instalación tradicional

1. **Crear archivo de configuración MCP**:

```json
{
  "mcpServers": {
    "mcp-boe": {
      "command": "/ruta/a/tu/conda/envs/tu_env/bin/python",
      "args": ["-m", "mcp_boe.server"],
      "env": {
        "PYTHONPATH": "/ruta/a/tu/MCP-BOE/src"
      }
    }
  }
}
```

2. **Configurar en Claude Code**:
```
/config-mcp /ruta/a/tu/claude_mcp_config.json
```

3. **Usar en Claude**:
```
¿Puedes buscar información sobre la Ley 40/2015?
Muéstrame el sumario del BOE de esta semana
¿Qué departamentos contienen la palabra "Ministerio"?
```

### Ollama + Open WebUI

```bash
# Instalar Open WebUI
pip install open-webui

# Configurar variables de entorno
export PYTHONPATH=/ruta/a/tu/MCP-BOE/src

# Iniciar servicios
ollama serve &
open-webui serve
```

## 🌐 API REST

Para usar desde aplicaciones web, móviles o cualquier cliente HTTP:

### Iniciar el servidor API

```bash
python rest_api_wrapper.py
```

La API estará disponible en: `http://localhost:8000`
Documentación interactiva: `http://localhost:8000/docs`

### Endpoints Disponibles

#### 🔍 Buscar Legislación
```bash
curl -X POST "http://localhost:8000/search/legislation" \
-H "Content-Type: application/json" \
-d '{"query": "Constitución Española", "limit": 5}'
```

#### 📰 Sumario del BOE
```bash
curl -X POST "http://localhost:8000/summary/boe" \
-H "Content-Type: application/json" \
-d '{"max_items": 10}'
```

#### 🏛️ Buscar Departamentos  
```bash
curl -X POST "http://localhost:8000/auxiliary/departments" \
-H "Content-Type: application/json" \
-d '{"search_term": "Ministerio", "limit": 10}'
```

#### 🔢 Descripción de Código
```bash
curl "http://localhost:8000/auxiliary/code/7723"
```

## 💡 Ejemplos

### Búsqueda de Legislación

```python
from mcp_boe import BOEHTTPClient
from mcp_boe.tools.legislation import LegislationTools

async def buscar_ley():
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Buscar Ley 40/2015
        resultados = await tools.search_consolidated_legislation({
            "query": "Ley 40/2015",
            "limit": 3
        })
        
        for resultado in resultados:
            print(resultado.text)
```

### Obtener Sumario del BOE

```python
from mcp_boe.tools.summaries import SummaryTools
from datetime import datetime, timedelta

async def sumario_boe():
    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)
        
        # Sumario de hace 3 días
        fecha = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
        
        resultados = await tools.get_boe_summary({
            "date": fecha,
            "max_items": 5
        })
        
        for resultado in resultados:
            print(resultado.text)
```

### Consultar Departamentos

```python
from mcp_boe.tools.auxiliary import AuxiliaryTools

async def buscar_departamentos():
    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)
        
        # Buscar ministerios
        resultados = await tools.get_departments_table({
            "search_term": "Ministerio",
            "limit": 10
        })
        
        for resultado in resultados:
            print(resultado.text)
```

## 🔧 Herramientas Disponibles

### 📜 Legislación Consolidada

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `search_consolidated_legislation` | Buscar en legislación consolidada | `query`, `limit`, `offset` |
| `get_consolidated_law` | Obtener norma específica | `law_id`, `include_metadata`, `include_analysis`, `include_full_text` |
| `get_law_structure` | Ver estructura de una norma | `law_id` |

### 📰 Sumarios BOE/BORME

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `get_boe_summary` | Sumario del BOE por fecha | `date`, `max_items` |
| `get_borme_summary` | Sumario del BORME por fecha | `date`, `max_items` |
| `search_recent_boe` | Buscar en BOE reciente | `days_back`, `search_terms` |

### 🏛️ Tablas Auxiliares

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `get_departments_table` | Códigos de departamentos | `search_term`, `limit` |
| `get_legal_ranges_table` | Rangos normativos | `limit` |
| `get_code_description` | Descripción de código específico | `code` |
| `search_auxiliary_data` | Buscar en todas las tablas | `query` |

## 🧪 Testing

```bash
# Todas las pruebas
python examples/basic_usage.py all

# Prueba rápida
python examples/basic_usage.py quick

# Prueba específica
python examples/basic_usage.py search
python examples/basic_usage.py summary
python examples/basic_usage.py departments
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Desarrollo Local

```bash
# Configurar entorno de desarrollo
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -e .

# Ejecutar tests
python -m pytest tests/

# Linting
python -m black src/
python -m flake8 src/
```

## 📊 Estructura del Proyecto

```
MCP-BOE/
├── src/mcp_boe/           # Código fuente principal
│   ├── models/            # Modelos Pydantic
│   ├── tools/            # Herramientas MCP
│   ├── utils/            # Utilidades (cliente HTTP)
│   └── server.py         # Servidor MCP principal
├── examples/             # Ejemplos de uso
├── tests/               # Pruebas unitarias
├── pyproject.toml       # Configuración del proyecto y dependencias
├── rest_api_wrapper.py  # API REST opcional
└── README.md           # Este archivo
```

## 🔒 Seguridad

- **Sin autenticación requerida**: La API del BOE es pública
- **Rate limiting**: Respeta los límites de la API oficial
- **Datos oficiales**: Toda la información proviene directamente del BOE
- **Sin almacenamiento**: No se almacenan datos localmente

## 📚 Documentación Adicional

- [API Oficial del BOE](https://www.boe.es/datosabiertos/documentos/Manual_API.pdf)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)

## 🐛 Solución de Problemas

### Error: "No module named 'mcp_boe'"
```bash
export PYTHONPATH="${PYTHONPATH}:/ruta/a/tu/MCP-BOE/src"
```

### Error: "Connection refused"
Verificar conectividad con la API del BOE:
```bash
python examples/basic_usage.py connectivity
```

### Error: Pydantic v2 warnings
Las advertencias de Pydantic v2 son normales y no afectan la funcionalidad.

## 📝 Changelog

### v0.1.0 (2025-08-23)
- ✅ Implementación inicial del servidor MCP
- ✅ Soporte para legislación consolidada
- ✅ Sumarios del BOE y BORME  
- ✅ Tablas auxiliares
- ✅ API REST wrapper
- ✅ Ejemplos y documentación

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Víctor Viloria**
- Email: vvictor.97@gmail.com
- GitHub: [@ComputingVictor](https://github.com/ComputingVictor)

## 🙏 Agradecimientos

- Al **Boletín Oficial del Estado** por proporcionar una API pública
- Al equipo de **Anthropic** por el protocolo MCP
- A la comunidad **Python** por las excelentes librerías

---

**¿Tienes preguntas?** Abre un [issue](https://github.com/ComputingVictor/MCP-BOE/issues) o envía un [pull request](https://github.com/ComputingVictor/MCP-BOE/pulls).

**¿Te gusta el proyecto?** ¡Dale una ⭐ en GitHub!
