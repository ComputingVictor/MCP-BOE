# RPVEA Framework para MCP-BOE-Consolidada
## Research → Prepare → Validate → Execute → Assess

**Versión:** 1.1
**Fecha:** 2025-11-23
**Adaptado de:** GVA RPVEA Framework 2.0
**Proyecto:** MCP-BOE-Consolidada

---

## 🎯 PROPÓSITO

Este framework adapta la metodología RPVEA del proyecto GVA ArcGIS MCP para el testing y desarrollo del servidor MCP-BOE-Consolidada. La regla fundamental:

> **"5 minutos en R (Research) ahorran 30 minutos en E/V (Execute/Validate)"**

---

## 🔀 TIPOS DE TESTS: CONFORMIDAD vs CALIDAD

### Distinción Fundamental

El MCP-BOE puede verse desde dos perspectivas:
- **Como pass-through**: Expone la API del BOE tal cual
- **Como capa de valor añadido**: Mejora la experiencia sobre la API

Esta distinción es crítica para definir qué es un "bug" vs qué es una "mejora potencial".

### Tests de Conformidad (Tipo C)

**Pregunta:** ¿El MCP expone correctamente la API del BOE?

| Aspecto | Criterio de éxito |
|---------|-------------------|
| Parámetros | Se pasan correctamente a la API |
| Respuesta | Se parsea sin pérdida de datos |
| Errores | Se propagan adecuadamente |
| Tipos | Coinciden con schema Pydantic |

**Resultado esperado:** La respuesta del MCP es equivalente a llamar la API directamente.

**Si falla:** Es un **BUG** del MCP que debe corregirse.

### Tests de Calidad (Tipo Q)

**Pregunta:** ¿Los resultados son útiles para el usuario final?

| Aspecto | Criterio de evaluación |
|---------|------------------------|
| Relevancia | ¿Los primeros resultados son los más relevantes? |
| Completitud | ¿Se obtiene toda la información necesaria? |
| Usabilidad | ¿Es fácil encontrar lo que se busca? |
| Performance | ¿Los tiempos son aceptables? |

**Resultado esperado:** Documentar comportamiento actual y gaps de usabilidad.

**Si hay gap:** Es una **MEJORA POTENCIAL** a evaluar para implementación.

### Matriz de Clasificación

```
┌─────────────────────────────────────────────────────────────┐
│                    RESULTADO DEL TEST                       │
├─────────────────────┬───────────────────────────────────────┤
│                     │  Conformidad (C)  │   Calidad (Q)     │
├─────────────────────┼───────────────────┼───────────────────┤
│ PASS                │ ✅ Funciona bien  │ ✅ Útil tal cual  │
├─────────────────────┼───────────────────┼───────────────────┤
│ FAIL                │ 🐛 BUG → Fix      │ 📋 Gap → Evaluar  │
├─────────────────────┼───────────────────┼───────────────────┤
│ Acción si falla     │ Corregir código   │ Documentar +      │
│                     │ obligatoriamente  │ decidir si mejora │
└─────────────────────┴───────────────────┴───────────────────┘
```

### Ejemplos Prácticos

#### Test de Conformidad:
```
Test C-1.1: Búsqueda simple
- Input: query="Ley 40/2015"
- Verificar: ¿MCP devuelve mismos resultados que API directa?
- Si difiere: BUG en parsing o paso de parámetros
```

#### Test de Calidad:
```
Test Q-1.1: Relevancia de búsqueda genérica
- Input: query="protección de datos"
- Verificar: ¿LOPD aparece en top 3 resultados?
- Si no: Documentar como gap de relevancia
- Decisión: ¿Implementar ranking propio? (feature nueva)
```

### Flujo de Decisión Post-Test

```
                    ┌──────────────┐
                    │ Ejecutar Test│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ ¿Tipo C o Q? │
                    └──────┬───────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
   ┌──────▼──────┐                  ┌───────▼──────┐
   │ Conformidad │                  │   Calidad    │
   └──────┬──────┘                  └───────┬──────┘
          │                                 │
   ┌──────▼──────┐                  ┌───────▼──────┐
   │  ¿Pasó?     │                  │   ¿Pasó?     │
   └──────┬──────┘                  └───────┬──────┘
          │                                 │
    ┌─────┴─────┐                     ┌─────┴─────┐
    │           │                     │           │
┌───▼───┐  ┌────▼────┐          ┌─────▼───┐  ┌────▼────┐
│  ✅   │  │   🐛    │          │   ✅    │  │   📋    │
│ PASS  │  │  BUG    │          │  PASS   │  │   GAP   │
│       │  │ Fix     │          │         │  │Documentar│
│       │  │Requerido│          │         │  │ Evaluar │
└───────┘  └─────────┘          └─────────┘  └─────────┘
```

### Registro en test_registry.json

```json
{
  "test_id": "1.1",
  "type": "C",  // "C" = Conformidad, "Q" = Calidad
  "name": "busqueda_simple_conformidad",
  "question": "¿El MCP pasa correctamente los parámetros a la API?",
  "success_criteria": "Respuesta MCP == Respuesta API directa",
  "if_fails": "BUG - requiere fix"
}
```

```json
{
  "test_id": "1.1Q",
  "type": "Q",
  "name": "busqueda_simple_calidad",
  "question": "¿La búsqueda genérica devuelve resultados útiles?",
  "success_criteria": "Ley buscada en top 3 resultados",
  "if_fails": "GAP - evaluar mejora de ranking"
}
```

### Documentación de Gaps de Calidad

Para cada gap identificado, crear entrada en `quality_gaps.json`:

```json
{
  "gap_id": "GAP-001",
  "discovered_in_test": "Q-1.1",
  "title": "Búsquedas genéricas no priorizan por relevancia",
  "description": "Buscar 'protección de datos' no devuelve LOPD en primeros resultados",
  "current_behavior": "Ordenamiento por fecha de publicación",
  "desired_behavior": "Ordenamiento por relevancia textual",
  "impact": "medio",
  "effort_estimate": "alto",
  "implementation_options": [
    {
      "option": "A",
      "description": "Documentar como limitación de API BOE",
      "effort": "bajo",
      "pros": ["Sin cambios de código", "Sin mantenimiento"],
      "cons": ["UX subóptima"]
    },
    {
      "option": "B",
      "description": "Implementar re-ranking en MCP",
      "effort": "alto",
      "pros": ["Mejor UX"],
      "cons": ["Mantenimiento", "Posible divergencia con API"]
    }
  ],
  "decision": null,
  "decision_date": null,
  "decision_rationale": null
}

---

## 📋 FASES RPVEA ADAPTADAS PARA BOE

### FASE R: RESEARCH (Investigación) - 10-15 min

**Objetivo:** Entender completamente antes de actuar.

#### Checklist R-BOE:
- [ ] Revisar documentación API BOE para el endpoint a probar
- [ ] Verificar estructura de datos esperada
- [ ] Identificar parámetros y sus tipos
- [ ] Buscar ejemplos de respuestas en documentación
- [ ] Consultar código existente en `src/mcp_boe/`
- [ ] Revisar tests similares ya ejecutados

#### Reglas críticas:
1. **NUNCA asumir, SIEMPRE verificar**
2. Si la API devuelve XML, entender la estructura XML antes de parsear
3. Si un campo es opcional, verificar comportamiento con/sin él

#### Deliverables R:
- Documentación del endpoint objetivo
- Estructura de request/response esperada
- Lista de edge cases identificados

---

### FASE P: PREPARE (Preparación) - 5-10 min

**Objetivo:** Preparar todo antes de ejecutar.

#### Checklist P-BOE:
- [ ] Crear directorio del test: `test_X.Y_nombre/`
- [ ] Preparar `input.json` con parámetros exactos
- [ ] Definir expectativas en `expected_behavior`
- [ ] Identificar normativa de referencia (BOE-A-XXXX-XXXXX)
- [ ] Verificar que el MCP server está activo

#### Estructura input.json:
```json
{
  "test_id": "1.1",
  "test_name": "busqueda_simple",
  "rpvea_session": "S001",
  "timestamp_prepared": "2025-11-23T17:41:11Z",
  "tool": "search_consolidated_legislation",
  "parameters": {
    "query": "Ley 40/2015",
    "limit": 5
  },
  "expected_behavior": "Debe devolver la Ley 40/2015 en los primeros resultados",
  "reference_law_id": "BOE-A-2015-10566",
  "triple_validation": {
    "v1_schema": "pending",
    "v2_api": "pending",
    "v3_real": "pending"
  }
}
```

#### Deliverables P:
- Directorio test creado
- `input.json` preparado
- Expectativas documentadas

---

### FASE V: VALIDATE (Validación) - 5-15 min

**Objetivo:** Triple Validación antes de código en producción.

#### TRIPLE VALIDACIÓN BOE:

##### V1: Validación de Schema (Pydantic)
**¿Qué valida?** Estructura de datos del modelo
**Cómo validar:**
```python
# Verificar modelos en src/mcp_boe/models/boe_models.py
# Comprobar campos requeridos y opcionales
# Validar tipos de datos
```
**Resultado:** ✅ Schema válido / ❌ Schema con errores

##### V2: Validación de API (Endpoint)
**¿Qué valida?** Respuesta real de la API del BOE
**Cómo validar:**
```bash
# Probar endpoint directamente
curl "https://www.boe.es/datosabiertos/api/legislacion-consolidada?query=Ley%2040/2015"
```
**Resultado:** ✅ API responde correctamente / ❌ Error de API

##### V3: Validación Real (Query Test)
**¿Qué valida?** Comportamiento real con datos reales
**Cómo validar:**
- Ejecutar herramienta MCP con parámetros reales
- Verificar que los datos devueltos son correctos y relevantes
- Comparar con expectativas definidas en P

**Resultado:** ✅ Test PASS / ⚠️ PARTIAL / ❌ FAIL

#### Matriz de decisión:
| V1 | V2 | V3 | Acción |
|----|----|----|--------|
| ✅ | ✅ | ✅ | Proceder con confianza |
| ✅ | ✅ | ❌ | Investigar discrepancia en datos |
| ✅ | ❌ | - | Bug en integración API |
| ❌ | - | - | Fix modelo Pydantic primero |

#### Deliverables V:
- Resultado V1, V2, V3 documentado
- Decisión de proceder o no

---

### FASE E: EXECUTE (Ejecución) - 15-30 min

**Objetivo:** Ejecutar tests de forma sistemática.

#### Checklist E-BOE:
- [ ] Capturar timestamp inicio
- [ ] Ejecutar herramienta MCP
- [ ] Capturar respuesta completa en `raw_response.json`
- [ ] Calcular latencia
- [ ] Procesar datos en `parsed_output.json`
- [ ] Capturar timestamp fin

#### Proceso de ejecución:
1. **Pre-flight check:**
   - ¿V1, V2, V3 pasaron? Si no, no ejecutar.
   - ¿Parámetros correctos en input.json?

2. **Ejecución:**
   - Usar la herramienta MCP apropiada
   - Observar comportamiento
   - Capturar TODA la respuesta

3. **Post-ejecución:**
   - Guardar raw_response.json
   - Procesar en parsed_output.json
   - Calcular métricas

#### Deliverables E:
- `raw_response.json` completo
- `parsed_output.json` procesado
- Métricas básicas calculadas

---

### FASE A: ASSESS (Evaluación) - 10-15 min

**Objetivo:** Evaluar resultados y documentar aprendizajes.

#### Checklist A-BOE:
- [ ] Determinar resultado: PASS / PARTIAL / FAIL
- [ ] Calcular métricas de calidad
- [ ] Identificar errores o bugs
- [ ] Documentar insights y lecciones
- [ ] Comparar con expectativas
- [ ] Proponer mejoras si aplica
- [ ] Actualizar TEST_REGISTRY.json

#### Documento ANALISIS_test_X.X.md:
```markdown
# ANÁLISIS TEST X.X - [Nombre]

## RPVEA Session: SXXX
## Fecha: YYYY-MM-DD

### Triple Validación
- V1 (Schema): ✅/❌
- V2 (API): ✅/❌
- V3 (Real): ✅/❌

### Resultado: PASS/PARTIAL/FAIL

### Métricas
- Latencia: XXX ms
- Tamaño respuesta: XX KB
- Relevancia: X.XX

### Lecciones Aprendidas
- [Lección 1]
- [Lección 2]

### Errores Detectados
- [Error 1] - Severidad: [baja/media/alta/crítica]

### Recomendaciones
- [Recomendación 1]
```

#### Deliverables A:
- `ANALISIS_test_X.X.md` completo
- TEST_REGISTRY.json actualizado
- Lecciones documentadas

---

## 📊 TEST REGISTRY SYSTEM

### Estructura test_registry.json:

```json
{
  "version": "1.0",
  "project": "mcp-boe-consolidada",
  "last_updated": "2025-11-23T17:41:11Z",
  "tests": {
    "1.1": {
      "name": "busqueda_simple",
      "level": 1,
      "status": "pending",
      "rpvea_session": null,
      "last_run": null,
      "result": null,
      "triple_validation": {
        "v1": null,
        "v2": null,
        "v3": null
      },
      "baseline": {
        "latency_ms": null,
        "relevance": null
      }
    }
  },
  "statistics": {
    "total": 0,
    "pass": 0,
    "partial": 0,
    "fail": 0,
    "pending": 0
  }
}
```

### Workflow de registro:

1. **Pre-cambio:** Registrar baseline actual
2. **Post-cambio:** Ejecutar regression tests
3. **Comparar:** Detectar regresiones
4. **Documentar:** Actualizar registry

---

## 🔄 SESSION DOCUMENTATION

### Formato SESSION_XX.md:

```markdown
# SESSION XX - [Título descriptivo]
## Fecha: YYYY-MM-DD
## RPVEA Phase: [R/P/V/E/A]

### Objetivo de la sesión
[Descripción breve]

### Tests ejecutados
| Test ID | Nombre | Resultado | Duración |
|---------|--------|-----------|----------|
| 1.1 | busqueda_simple | PASS | 5 min |

### Bugs encontrados
- [BUG-001] APIError hereda de BaseModel en lugar de Exception

### Lecciones aprendidas
1. **[Categoría]:** [Lección]

### Próximos pasos
- [ ] Tarea 1
- [ ] Tarea 2
```

---

## ⚠️ REGLAS CRÍTICAS RPVEA-BOE

### NUNCA:
1. ❌ Ejecutar tests sin completar R y P
2. ❌ Modificar código sin Triple Validación
3. ❌ Asumir que la API devuelve lo esperado
4. ❌ Ignorar errores "menores" - documentar TODO
5. ❌ Saltarse la fase A (assessment)

### SIEMPRE:
1. ✅ Investigar antes de ejecutar
2. ✅ Validar schema, API, y real query
3. ✅ Documentar cada test completamente
4. ✅ Actualizar test registry después de cada test
5. ✅ Capturar lecciones aprendidas

### SI ENCUENTRAS UN BUG:
1. **STOP** - No continuar con más tests
2. **DOCUMENT** - Registrar el bug detalladamente
3. **ASSESS** - ¿Es bloqueante para otros tests?
4. **DECIDE** - ¿Fix inmediato o continuar documentando?
5. **TRACK** - Agregar a lista de bugs pendientes

---

## 📈 INTEGRACIÓN CON CI/CD

### Pre-commit hooks:
- Validar que test_registry.json está actualizado
- Verificar formato de documentación

### GitHub Actions:
- Ejecutar regression tests en PR
- Comparar con baseline
- Alertar si hay regresiones

### Scripts de soporte:
```bash
# Registrar nuevo test
python scripts/register_test.py --id 1.1 --name busqueda_simple

# Ejecutar regression tests
python scripts/run_regression.py --level 1

# Generar informe de nivel
python scripts/generate_report.py --level 1
```

---

## 📂 ESTRUCTURA DE DIRECTORIOS ACTUALIZADA

```
testing_mcp_boe_consolidada/
├── 00_estructura/
│   ├── PLAN_BANCO_PRUEBAS_MCP_BOE_CONSOLIDADA.md
│   ├── METODOLOGIA_DOCUMENTACION.md
│   ├── RPVEA_BOE_FRAMEWORK.md (este archivo)
│   ├── test_registry.json
│   ├── test_history.json
│   └── PLANTILLAS/
│       ├── template_test.md
│       ├── template_nivel.md
│       ├── template_session.md
│       └── template_informe_final.md
│
├── sessions/
│   ├── SESSION_001.md
│   ├── SESSION_002.md
│   └── ...
│
├── 01_nivel_basico/
│   ├── test_1.1_busqueda_simple/
│   │   ├── input.json
│   │   ├── raw_response.json
│   │   ├── parsed_output.json
│   │   └── ANALISIS_test_1.1.md
│   └── INFORME_NIVEL_1.md
│
├── ... (niveles 02-08)
│
└── bugs/
    ├── BUG-001_apierror_inheritance.md
    └── ...
```

---

## 🚀 QUICK START

### Para iniciar una sesión de testing:

1. **Research (5 min):**
   ```bash
   # Leer documentación del endpoint
   # Revisar código existente
   ```

2. **Prepare (3 min):**
   ```bash
   mkdir -p 01_nivel_basico/test_1.1_busqueda_simple
   # Crear input.json
   ```

3. **Validate (5 min):**
   ```bash
   # V1: Revisar modelo Pydantic
   # V2: Probar API directamente
   # V3: Preparar query real
   ```

4. **Execute (5 min):**
   ```bash
   # Ejecutar herramienta MCP
   # Capturar respuesta
   ```

5. **Assess (5 min):**
   ```bash
   # Documentar resultado
   # Actualizar registry
   ```

---

## 📝 CHANGELOG

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2025-11-23 | Versión inicial adaptada de GVA RPVEA |
| 1.1 | 2025-11-23 | Añadida distinción Tests Conformidad (C) vs Calidad (Q) |

---

**FIN DEL FRAMEWORK RPVEA-BOE**

*"Prototype First, Code Second"*
*"Bug ≠ Gap: Conformidad es obligatorio, Calidad es decisión"*
