# Limitaciones de la API del BOE

Este documento describe las limitaciones conocidas de la API del BOE y cómo el proyecto MCP-BOE maneja estas restricciones.

## Resumen de Limitaciones

| Funcionalidad | Estado | Observación |
|---------------|--------|-------------|
| **Búsqueda por texto en legislación** | ❌ NO funciona | La API acepta queries pero devuelve resultados incorrectos |
| **Obtener norma por ID** | ✅ Funciona | Acceso directo a normas específicas |
| **Listar legislación** | ✅ Funciona | Listado con filtros por fecha |
| **Búsqueda en sumarios** | ✅ Funciona | Búsqueda local en contenido descargado |
| **Filtro por departamento** | ✅ Funciona | Usando códigos específicos |
| **Filtro por rango legal** | ✅ Funciona | Usando códigos específicos |

## Problema Principal: Búsqueda por Texto

### Descripción del Problema
La API de legislación consolidada (`/legislacion-consolidada`) acepta queries de búsqueda en formato JSON, pero **ignora completamente el contenido de búsqueda** y devuelve resultados que no corresponden con los términos buscados.

### Ejemplo del Problema
```python
# Búsqueda solicitada
query = {"query": {"query_string": {"query": "texto:\"Constitución\""}}}

# Resultado esperado: Constitución Española
# Resultado obtenido: Ley de Aguas de Aragón (u otras normas aleatorias)
```

### Causa Técnica
La API acepta el formato de query correctamente (no devuelve error), pero parece no procesar el contenido de búsqueda, devolviendo en su lugar un conjunto predeterminado o aleatorio de resultados.

## Soluciones Alternativas

### 1. Usar IDs Específicos
Para acceder a normas conocidas, use directamente su identificador BOE:

```python
# Ejemplos de IDs importantes
constitución = "BOE-A-1978-31229"
lopdgdd = "BOE-A-2018-16673" 
ley_39_2015 = "BOE-A-2015-10565"
ley_40_2015 = "BOE-A-2015-10566"
```

### 2. Búsqueda en Sumarios
La búsqueda en sumarios diarios **SÍ funciona** porque se realiza localmente sobre el contenido descargado:

```python
# Buscar en el sumario de una fecha específica
from mcp_boe import search_summaries
results = await search_summaries(date="20240115", search_text="protección datos")
```

### 3. Filtros por Metadatos
Use filtros por departamento, rango legal o fechas en lugar de búsqueda por texto:

```python
# Filtrar por departamento y rango
results = await search_consolidated_legislation(
    department_code="7723",  # Jefatura del Estado
    legal_range_code="1300",  # Ley
    from_date="20230101",
    to_date="20231231"
)
```

## APIs Disponibles

### API de Legislación Consolidada
- **Endpoint**: `/legislacion-consolidada`
- **Funciona**: Acceso por ID, listados, filtros por fecha
- **NO funciona**: Búsqueda por texto

### API de Sumarios
- **Endpoint**: `/boe/sumario/{fecha}`
- **Funciona**: Todo, incluida búsqueda por texto (procesamiento local)
- **Útil para**: Publicaciones recientes, novedades diarias

## Recomendaciones para Usuarios

1. **Para buscar normas específicas**: Use el ID directo si lo conoce
2. **Para explorar legislación reciente**: Use la búsqueda en sumarios
3. **Para listar legislación**: Use filtros por fecha, departamento o rango
4. **Evite**: Confiar en la búsqueda por texto en legislación consolidada

## Estado del Proyecto

El proyecto MCP-BOE funciona correctamente dentro de las limitaciones de la API del BOE. Las limitaciones documentadas aquí son inherentes a la API del BOE, no al proyecto MCP-BOE.

## Contacto y Reportes

Si encuentra otras limitaciones o tiene información sobre cómo mejorar las búsquedas, por favor:
- Abra un issue en el repositorio
- Incluya ejemplos específicos de queries y respuestas
- Sugiera alternativas o mejoras

---

*Última actualización: Agosto 2025*