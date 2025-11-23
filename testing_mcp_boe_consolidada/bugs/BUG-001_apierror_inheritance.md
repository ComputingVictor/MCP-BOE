# BUG-001: APIError hereda de BaseModel en lugar de Exception

**ID:** BUG-001
**Severidad:** CRÍTICA
**Estado:** OPEN
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

- [ ] Modificar clase APIError en boe_models.py
- [ ] Actualizar imports si es necesario
- [ ] Verificar usos en http_client.py
- [ ] Verificar usos en tools/
- [ ] Ejecutar tests unitarios existentes
- [ ] Ejecutar test 2.1 para validar fix
- [ ] Actualizar estado del bug a FIXED

---

## 📝 Historial

| Fecha | Acción | Autor |
|-------|--------|-------|
| 2025-11-23 | Bug descubierto durante test 2.1 | pepo |
| 2025-11-23 | Documentación creada | claude |
| - | Fix aplicado | - |
| - | Bug cerrado | - |

---

**Prioridad de fix:** ALTA - Bloquea múltiples tests
