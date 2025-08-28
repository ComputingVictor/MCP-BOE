#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras en el manejo de errores.
"""

import asyncio
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mcp_boe.utils.http_client import BOEHTTPClient, APIError
from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.utils.warnings_handler import BOEWarnings


async def test_invalid_parameters():
    """Prueba el manejo de parámetros inválidos."""
    print("\n" + "=" * 70)
    print("TEST 1: Parámetros Inválidos")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Test 1: Fecha inválida
        print("\n1. Probando fecha inválida:")
        result = await tools.search_consolidated_legislation({
            "from_date": "2024-01-01",  # Formato incorrecto
            "limit": 1
        })
        print(result[0].text[:200])
        
        # Test 2: ID inválido
        print("\n2. Probando ID de ley inválido:")
        result = await tools.get_consolidated_law({
            "law_id": "BOE-X-INVALIDO"
        })
        print(result[0].text[:200])
    
    return True


async def test_search_warnings():
    """Prueba las advertencias de búsqueda."""
    print("\n" + "=" * 70)
    print("TEST 2: Advertencias de Búsqueda")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Búsqueda que probablemente devuelva resultados incorrectos
        print("\n1. Buscando 'Constitución Española':")
        result = await tools.search_consolidated_legislation({
            "query": "Constitución Española",
            "limit": 2
        })
        
        # Verificar que incluye advertencias
        result_text = result[0].text
        
        if "⚠️" in result_text:
            print("✅ Advertencia incluida en los resultados")
        else:
            print("❌ No se incluyó advertencia")
        
        if "limitaciones" in result_text.lower():
            print("✅ Menciona limitaciones de la API")
        else:
            print("❌ No menciona limitaciones")
        
        if "BOE-A-1978-31229" in result_text:
            print("✅ Sugiere ID directo de la Constitución")
        else:
            print("❌ No sugiere ID directo")
    
    return True


async def test_no_results_message():
    """Prueba el mensaje cuando no hay resultados."""
    print("\n" + "=" * 70)
    print("TEST 3: Mensaje de No Resultados")
    print("=" * 70)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Búsqueda muy específica que probablemente no devuelva resultados
        result = await tools.search_consolidated_legislation({
            "query": "zzzzxxxxwwww",
            "from_date": "20240101",
            "to_date": "20240105",
            "limit": 1
        })
        
        result_text = result[0].text
        print("Mensaje de no resultados:")
        print(result_text[:300])
        
        if "No se encontraron" in result_text or "📭" in result_text:
            print("\n✅ Mensaje de no resultados apropiado")
        else:
            print("\n❌ Mensaje de no resultados inadecuado")
    
    return True


async def test_validation_detection():
    """Prueba la detección de resultados incorrectos."""
    print("\n" + "=" * 70)
    print("TEST 4: Detección de Resultados Incorrectos")
    print("=" * 70)
    
    from mcp_boe.utils.warnings_handler import SearchResultValidator
    
    # Simular resultados que no coinciden
    fake_results = [
        {"titulo": "Real Decreto sobre Aguas", "identificador": "BOE-A-2024-123"},
        {"titulo": "Ley de Comercio", "identificador": "BOE-A-2024-456"},
        {"titulo": "Orden Ministerial de Sanidad", "identificador": "BOE-A-2024-789"}
    ]
    
    validation = SearchResultValidator.validate_search_results(
        "Constitución Española",
        fake_results,
        log_mismatches=False
    )
    
    print(f"Búsqueda: {validation['search_text']}")
    print(f"Resultados coincidentes: {validation['matching_results']}/{validation['total_results']}")
    print(f"Confianza: {validation['confidence']:.0%}")
    print(f"Probablemente incorrecto: {validation['likely_incorrect']}")
    
    if validation['likely_incorrect']:
        print("✅ Detecta correctamente resultados no relacionados")
    else:
        print("❌ No detecta resultados incorrectos")
    
    return True


async def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 70)
    print("PRUEBAS DE MANEJO DE ERRORES Y ADVERTENCIAS")
    print("=" * 70)
    
    tests = [
        ("Parámetros Inválidos", test_invalid_parameters),
        ("Advertencias de Búsqueda", test_search_warnings),
        ("Mensaje No Resultados", test_no_results_message),
        ("Detección de Incorrectos", test_validation_detection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASADO" if success else "❌ FALLADO"
        print(f"{status}: {name}")
    
    print(f"\n{'✅' if passed == total else '⚠️'} {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡El manejo de errores funciona correctamente!")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)