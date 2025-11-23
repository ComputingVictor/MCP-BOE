# METODOLOGÍA DE DOCUMENTACIÓN
## Banco de Pruebas MCP-BOE-CONSOLIDADA

**Versión:** 1.0  
**Fecha:** 2025-11-23  
**Autor:** pepo  
**Device:** MacBook-Air-de-Pepo.local

---

## 🎯 OBJETIVOS DEL SISTEMA DE DOCUMENTACIÓN

1. **Trazabilidad Completa**
   - Cada test documentado desde entrada hasta resultado
   - Cadena de evidencia verificable
   - Reproducibilidad garantizada

2. **Análisis Comparativo**
   - Comparación con boe-mcp
   - Identificación de gaps
   - Scoring objetivo

3. **Aprendizaje Continuo**
   - Captura de insights
   - Identificación de patrones
   - Base de conocimiento

4. **Auditoría Técnica**
   - Evidencia de cada llamada
   - Métricas verificables
   - Conclusiones fundamentadas

---

## 📂 ESTRUCTURA DE ARCHIVOS POR TEST

### Archivos Obligatorios:

#### 1. `input.json`
**Propósito:** Registrar parámetros exactos enviados al MCP

**Formato:**
```json
{
  "test_id": "1.1",
  "test_name": "busqueda_simple",
  "timestamp": "2025-11-23T17:41:11Z",
  "tool": "search_consolidated_legislation",
  "parameters": {
    "query": "Ley 40/2015",
    "limit": 5,
    "offset": 0
  },
  "expected_behavior": "Debe devolver la Ley 40/2015 en primeros resultados"
}
```

#### 2. `raw_response.json`
**Propósito:** Capturar respuesta completa sin procesar

**Formato:**
```json
{
  "timestamp_received": "2025-11-23T17:41:12.345Z",
  "latency_ms": 1345,
  "status": "success",
  "raw_data": "...[respuesta completa del MCP]..."
}
```

#### 3. `parsed_output.json`
**Propósito:** Datos procesados y estructurados para análisis

**Formato:**
```json
{
  "test_id": "1.1",
  "parsed_at": "2025-11-23T17:41:13Z",
  "results": {
    "count": 5,
    "items": [...],
    "metadata": {...}
  },
  "quality_metrics": {
    "relevance": 0.95,
    "completeness": 1.0,
    "accuracy": 1.0
  }
}
```

#### 4. `ANALISIS_test_X.X.md`
**Propósito:** Análisis humano completo del test

**Secciones obligatorias:**
- Objetivo
- Input
- Métricas
- Output
- Resultado (PASS/PARTIAL/FAIL)
- Análisis detallado
- Insights
- Errores
- Comparación
- Recomendaciones

### Archivos Opcionales:

#### 5. `screenshots/`
**Cuándo crear:** Si hay visualización de datos o interfaz

**Naming convention:**
- `01_input_params.png`
- `02_response_data.png`
- `03_error_message.png`
- `04_comparison.png`

#### 6. `logs.txt`
**Cuándo crear:** Si hay debugging complejo o errores

**Contenido:**
- Console logs
- Error traces
- Debug output

---

## 📝 PROCESO DE DOCUMENTACIÓN PASO A PASO

### ANTES DE EJECUTAR EL TEST:

#### Paso 1: Crear estructura de directorios
```bash
mkdir -p 01_nivel_basico/test_1.X_nombre/screenshots
```

#### Paso 2: Preparar input.json
- Definir parámetros del test
- Documentar expectativas
- Timestamp de preparación

#### Paso 3: Revisar contexto
- ¿Qué valida este test?
- ¿Qué necesito observar?
- ¿Qué comparar con boe-mcp?

### DURANTE LA EJECUCIÓN:

#### Paso 4: Capturar timestamp inicio
```bash
date -u +'%Y-%m-%dT%H:%M:%SZ'
```

#### Paso 5: Ejecutar herramienta MCP
- Usar parámetros de input.json
- Observar comportamiento
- Notar peculiaridades

#### Paso 6: Capturar timestamp fin
```bash
date -u +'%Y-%m-%dT%H:%M:%SZ'
```

#### Paso 7: Guardar respuesta raw
- Copiar respuesta completa
- Guardar en raw_response.json
- Incluir metadatos de captura

### DESPUÉS DE LA EJECUCIÓN:

#### Paso 8: Procesar datos
- Parsear respuesta
- Extraer campos relevantes
- Calcular métricas
- Guardar en parsed_output.json

#### Paso 9: Capturar screenshots (si aplica)
- Input visible
- Response visible
- Errores visibles
- Comparaciones

#### Paso 10: Analizar resultado
- ¿Funcionó correctamente?
- ¿PASS / PARTIAL / FAIL?
- ¿Qué aprendí?
- ¿Qué mejorar?

#### Paso 11: Documentar análisis
- Usar template_test.md
- Completar todas las secciones
- Ser específico y objetivo
- Incluir evidencias

#### Paso 12: Actualizar checklist
- Marcar test como completado
- Actualizar progreso del nivel
- Verificar prerequisites para siguiente test

---

## 📊 CRITERIOS DE EVALUACIÓN

### Test Individual:

#### ✅ PASS (Aprobado)
**Criterios:**
- Respuesta recibida sin errores
- Estructura de datos correcta
- Contenido relevante y preciso
- Performance aceptable (<2s)
- Cobertura funcional completa

**Puntuación:** 100/100

#### ⚠️ PARTIAL (Parcial)
**Criterios:**
- Respuesta recibida con warnings
- Estructura correcta pero incompleta
- Contenido mayormente relevante
- Performance degradada (2-5s)
- Cobertura funcional limitada

**Puntuación:** 50-99/100

#### ❌ FAIL (Fallido)
**Criterios:**
- Error crítico en respuesta
- Estructura incorrecta
- Contenido irrelevante
- Timeout (>5s)
- Funcionalidad no disponible

**Puntuación:** 0-49/100

### Nivel Completo:

#### 🏆 EXCELENTE
- ≥90% tests PASS
- Sin bugs críticos
- Performance consistente
- Documentación completa

#### 👍 BUENO
- 70-89% tests PASS
- Bugs menores manejables
- Performance aceptable
- Documentación adecuada

#### 🤝 ACEPTABLE
- 50-69% tests PASS
- Algunos bugs críticos
- Performance irregular
- Documentación básica

#### 👎 DEFICIENTE
- <50% tests PASS
- Múltiples bugs críticos
- Performance inaceptable
- Documentación incompleta

---

## 📈 MÉTRICAS OBLIGATORIAS

### Por Test Individual:

#### Temporales:
- `timestamp_start`: ISO 8601
- `timestamp_end`: ISO 8601
- `latency_ms`: Entero
- `execution_time`: Segundos

#### Volumen:
- `response_size_bytes`: Entero
- `response_size_kb`: Float (2 decimales)
- `num_results`: Entero
- `depth_levels`: Entero (anidamiento)

#### Calidad:
- `relevance_score`: 0.0-1.0
- `completeness_score`: 0.0-1.0
- `accuracy_score`: 0.0-1.0
- `overall_score`: 0-100

#### Errores:
- `error_count`: Entero
- `warning_count`: Entero
- `error_severity`: [none, low, medium, high, critical]
- `error_messages`: Array de strings

### Por Nivel:

#### Agregadas:
- `total_tests`: Entero
- `pass_count`: Entero
- `partial_count`: Entero
- `fail_count`: Entero
- `pass_rate`: Porcentaje

#### Performance:
- `avg_latency_ms`: Float
- `median_latency_ms`: Float
- `p95_latency_ms`: Float
- `p99_latency_ms`: Float

#### Volumen:
- `total_data_processed_mb`: Float
- `avg_response_size_kb`: Float

---

## 🔄 WORKFLOW DE REVISIÓN

### Auto-revisión:
1. Completar checklist de secciones
2. Verificar evidencias incluidas
3. Confirmar métricas calculadas
4. Revisar ortografía y formato

### Validación cruzada:
1. Comparar con template
2. Verificar consistencia de datos
3. Confirmar reproducibilidad
4. Validar conclusiones

### Aprobación de nivel:
1. Revisar informe de nivel
2. Verificar todos los tests documentados
3. Confirmar criterios de éxito
4. Aprobar paso a siguiente nivel

---

## 📎 NOMENCLATURA Y CONVENCIONES

### Nombres de archivos:
- **Tests:** `test_X.Y_nombre_descriptivo/`
- **Inputs:** `input.json`
- **Outputs raw:** `raw_response.json`
- **Outputs parsed:** `parsed_output.json`
- **Análisis:** `ANALISIS_test_X.Y.md`
- **Screenshots:** `NN_descripcion.png`

### IDs de tests:
- **Formato:** `[nivel].[número]`
- **Ejemplo:** `1.1`, `1.2`, `2.1`

### Timestamps:
- **Formato:** ISO 8601 UTC
- **Ejemplo:** `2025-11-23T17:41:11Z`

### Paths:
- **Root:** `/Users/pepo/Documents/Proyectos/BOE/testing_mcp_boe_consolidada/`
- **Niveles:** `0X_nivel_nombre/`
- **Tests:** `test_X.Y_nombre/`

---

## ✅ CHECKLIST DE CALIDAD

### Antes de marcar test como completo:

- [ ] `input.json` creado con parámetros correctos
- [ ] `raw_response.json` guardado con respuesta completa
- [ ] `parsed_output.json` procesado con métricas
- [ ] `ANALISIS_test_X.X.md` completado con todas las secciones
- [ ] Screenshots capturados (si aplica)
- [ ] Métricas calculadas correctamente
- [ ] Resultado determinado (PASS/PARTIAL/FAIL)
- [ ] Comparación con boe-mcp documentada
- [ ] Insights y aprendizajes registrados
- [ ] Recomendaciones incluidas
- [ ] Formato markdown correcto
- [ ] Links funcionando
- [ ] Timestamp actualizado

### Antes de marcar nivel como completo:

- [ ] Todos los tests del nivel ejecutados
- [ ] Informe de nivel completo
- [ ] Métricas agregadas calculadas
- [ ] Comparativa consolidada
- [ ] Score del nivel determinado
- [ ] Decisión sobre siguiente nivel tomada
- [ ] Checklist de progreso actualizado

---

## 🚨 CASOS ESPECIALES

### Si un test falla críticamente:
1. Documentar el fallo detalladamente
2. Intentar identificar causa raíz
3. Buscar workaround si existe
4. Reportar al desarrollador si es bug
5. Marcar como bloqueante si impide progreso
6. Documentar impacto en nivel

### Si hay timeout:
1. Registrar tiempo transcurrido
2. Intentar con parámetros reducidos
3. Documentar comportamiento
4. Marcar como limitación de performance

### Si respuesta es inesperada:
1. Comparar con especificación API
2. Verificar si es bug o feature no documentado
3. Contrastar con boe-mcp
4. Documentar discrepancia

### Si test requiere prerequisitos:
1. Documentar dependencias
2. Verificar estado antes de ejecutar
3. Ejecutar setup necesario
4. Documentar en análisis

---

## 📌 MEJORES PRÁCTICAS

### Documentación:
- ✅ Ser específico y objetivo
- ✅ Incluir evidencias concretas
- ✅ Usar formato markdown consistente
- ✅ Agregar contexto suficiente
- ❌ No asumir conocimiento previo
- ❌ No usar lenguaje ambiguo

### Testing:
- ✅ Un test, un objetivo
- ✅ Parámetros bien documentados
- ✅ Resultados reproducibles
- ❌ No tests dependientes entre sí
- ❌ No asumir estado previo

### Análisis:
- ✅ Fundamentar conclusiones
- ✅ Comparar con alternativas
- ✅ Proponer mejoras concretas
- ❌ No hacer juicios sin evidencia
- ❌ No omitir limitaciones

---

**FIN DEL DOCUMENTO DE METODOLOGÍA**

---

*Metodología v1.0 - Banco Pruebas MCP-BOE-CONSOLIDADA*
