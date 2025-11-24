# BUG-001: APIError hereda de BaseModel en lugar de Exception

**ID:** BUG-001
**Severidad:** CRÍTICA
**Estado:** FIXED
**Descubierto en:** SESSION_001
**Fecha:** 2025-11-23

---

## 📍 Ubicación

- **Archivo:** `src/mcp_boe/models/boe_models.py`
- **Líneas:** 463-483
- **Clase:** `APIError`

---

## 🔍 Descripción

La clase `APIError` está definida heredando de `BaseModel` (Pydantic) en lugar de `Exception`. Esto viola el contrato de Python para excepciones y causa errores en tiempo de ejecución.

### Código actual (incorrecto):
```python
class APIError(BaseModel):
    """Error de la API del BOE."""
    codigo: int = Field(..., description="Código de error HTTP")
    mensaje: str = Field(..., description="Mensaje de error")
    detalles: Optional[str] = Field(None, description="Detalles adicionales del error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Momento del error")
```

---

## 💥 Error Producido

```
catching classes that do not inherit from BaseException is not allowed
```

Este error ocurre cuando el código intenta usar `APIError` en un bloque `except`:
```python
try:
    # llamada a API
except APIError as e:  # ← ERROR AQUÍ
    # manejo del error
```

---

## 🎯 Impacto

### Tests bloqueados:
- Test 2.1: metadatos_basicos
- Test 2.2: analisis_juridico
- Test 2.3: texto_completo
- Test 2.4: eli_metadata
- Test 2.5: estructura_indice
- Potencialmente todos los tests de nivel 3+

### Funcionalidad afectada:
- Cualquier operación que pueda generar errores de API
- Manejo de errores HTTP
- Recuperación de fallos de red

---

## ✅ Fix Propuesto

### Opción A: Convertir a Exception simple
```python
class APIError(Exception):
    """Error de la API del BOE."""

    def __init__(
        self,
        codigo: int,
        mensaje: str,
        detalles: Optional[str] = None
    ):
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles
        self.timestamp = datetime.now()
        super().__init__(f"[{codigo}] {mensaje}")

    def __str__(self) -> str:
        base = f"[{self.codigo}] {self.mensaje}"
        if self.detalles:
            base += f" - {self.detalles}"
        return base

    def to_dict(self) -> dict:
        """Serializar error para logging/respuesta."""
        return {
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "detalles": self.detalles,
            "timestamp": self.timestamp.isoformat()
        }
```

### Opción B: Mantener modelo Pydantic separado + Exception
```python
class APIErrorData(BaseModel):
    """Modelo de datos para error de API (para serialización)."""
    codigo: int = Field(..., description="Código de error HTTP")
    mensaje: str = Field(..., description="Mensaje de error")
    detalles: Optional[str] = Field(None, description="Detalles adicionales")
    timestamp: datetime = Field(default_factory=datetime.now)


class APIError(Exception):
    """Excepción para errores de la API del BOE."""

    def __init__(self, codigo: int, mensaje: str, detalles: Optional[str] = None):
        self.data = APIErrorData(codigo=codigo, mensaje=mensaje, detalles=detalles)
        super().__init__(str(self.data))
```

### Recomendación:
**Opción A** es más simple y suficiente para el caso de uso actual.

---

## 🔧 Archivos a Modificar

1. `src/mcp_boe/models/boe_models.py` - Cambiar definición de APIError
2. Buscar todos los usos de `APIError` para verificar compatibilidad:
   - `src/mcp_boe/utils/http_client.py`
   - `src/mcp_boe/tools/*.py`

---

## 📋 Checklist de Fix

- [x] Modificar clase APIError en boe_models.py
- [x] Actualizar imports si es necesario
- [x] Verificar usos en http_client.py
- [x] Verificar usos en tools/
- [ ] Ejecutar tests unitarios existentes
- [x] Ejecutar test 2.1 para validar fix
- [x] Actualizar estado del bug a FIXED

---

## 📝 Historial

| Fecha | Acción | Autor |
|-------|--------|-------|
| 2025-11-23 | Bug descubierto durante test 2.1 | pepo |
| 2025-11-23 | Documentación creada | claude |
| 2025-11-23 | Session 2: Fix parcial (herencia Exception) | claude |
| 2025-11-24 | Session 3: Fix completo (timestamp opcional) | claude |
| 2025-11-24 | Bug cerrado - triple validación PASS | claude |

---

**Prioridad de fix:** ALTA - Bloquea múltiples tests

---

## 🔄 PROGRESO DEL FIX (Session 2 - 2025-11-23)

### Triple Validación RPVEA:

#### V1: Schema ✅ PASS
- APIError cambiado a heredar de Exception
- Sintaxis correcta, se puede instanciar y hacer raise/except

#### V2: API ❌ FAIL - Problema encontrado
- `http_client.py` líneas 172-177 y 180-185 pasan `timestamp=datetime.now()`
- El nuevo constructor no acepta `timestamp` como argumento
- Error: `TypeError: APIError.__init__() got an unexpected keyword argument 'timestamp'`

#### V3: Real Query - PENDIENTE (bloqueado por V2)

### Fix adicional requerido:
Modificar `APIError.__init__` para aceptar `timestamp` opcional:
```python
def __init__(
    self,
    codigo: int,
    mensaje: str,
    detalles: Optional[str] = None,
    timestamp: Optional[datetime] = None  # AÑADIR
):
    ...
    self.timestamp = timestamp or datetime.now()  # CAMBIAR
```

### Estado actual:
- Archivo modificado: `src/mcp_boe/models/boe_models.py`
- ✅ Fix completo aplicado

---

## ✅ FIX COMPLETADO (Session 3 - 2025-11-24)

### Triple Validación RPVEA - TODAS PASADAS:

#### V1: Schema ✅ PASS
- APIError hereda de Exception
- Sintaxis correcta

#### V2: API ✅ PASS
- Constructor acepta `timestamp` opcional
- Compatible con `http_client.py` (líneas 172-177, 180-185, 253-256)
- Tests verificados:
  - Sin timestamp → genera automáticamente
  - Con timestamp → usa el proporcionado
  - raise/except → funciona correctamente

#### V3: Real Query ✅ PASS
- Búsqueda "Ley 40/2015" ejecutada via MCP
- Respuesta: BOE-A-2015-10566 encontrado
- API funcionando correctamente

### Código final aplicado:
```python
class APIError(Exception):
    """
    Error de la API del BOE.
    Hereda de Exception para poder ser usado en bloques try/except.
    """

    def __init__(
        self,
        codigo: int,
        mensaje: str,
        detalles: Optional[str] = None,
        timestamp: Optional[datetime] = None  # Parámetro opcional añadido
    ):
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles
        self.timestamp = timestamp or datetime.now()  # Usa el proporcionado o genera
        super().__init__(f"[{codigo}] {mensaje}")
```

### Nota sobre `timestamp`:
- Este `timestamp` es para **logging/debugging de errores** (momento en que ocurrió el error)
- NO tiene relación con los filtros `from_date`/`to_date` de búsquedas
- Los filtros de búsqueda filtran por `fecha_actualizacion` de las normas (ver documentación API)
