#!/usr/bin/env python3
"""
Script de pruebas para WordPress Security Auditor
"""

import asyncio
import httpx
import json
from main import WordPressSecurityChecker, SecurityHeaders

async def test_security_headers():
    """Prueba la validación de headers de seguridad"""
    print("🧪 Probando validación de headers de seguridad...")
    
    # Headers de ejemplo
    test_headers = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Type': 'text/html; charset=UTF-8'
    }
    
    results = SecurityHeaders.check_security_headers(test_headers)
    
    print("✅ Headers encontrados:")
    for header, data in results.items():
        status = "✅" if data['status'] == 'PASS' else "⚠️" if data['status'] == 'WARNING' else "❌"
        print(f"   {status} {header}: {data['status']}")
    
    return results

async def test_wordpress_checks():
    """Prueba las verificaciones de WordPress"""
    print("\n🧪 Probando verificaciones de WordPress...")
    
    # URL de prueba (usar un sitio de prueba real)
    test_url = "https://httpbin.org"  # Servicio de pruebas HTTP
    
    async with WordPressSecurityChecker() as checker:
        print("   🔍 Verificando wp-admin...")
        wp_admin_result = await checker.check_wp_admin_access(test_url)
        print(f"      Resultado: {wp_admin_result['status']} - {wp_admin_result['message']}")
        if 'risk_explanation' in wp_admin_result:
            print(f"      Riesgo: {wp_admin_result['risk_explanation'][:100]}...")
        
        print("   🔍 Verificando xmlrpc...")
        xmlrpc_result = await checker.check_xmlrpc_access(test_url)
        print(f"      Resultado: {xmlrpc_result['status']} - {xmlrpc_result['message']}")
        if 'risk_explanation' in xmlrpc_result:
            print(f"      Riesgo: {xmlrpc_result['risk_explanation'][:100]}...")
        
        print("   🔍 Verificando wp-config...")
        wp_config_result = await checker.check_wp_config_exposure(test_url)
        print(f"      Resultado: {wp_config_result['status']} - {wp_config_result['message']}")
        if 'risk_explanation' in wp_config_result:
            print(f"      Riesgo: {wp_config_result['risk_explanation'][:100]}...")
        
        print("   🔍 Verificando listado de directorios...")
        dir_listing_result = await checker.check_directory_listing(test_url)
        print(f"      Resultado: {dir_listing_result['status']} - {dir_listing_result['message']}")
        if 'risk_explanation' in dir_listing_result:
            print(f"      Riesgo: {dir_listing_result['risk_explanation'][:100]}...")
        
        print("   🔍 Verificando SSL...")
        ssl_result = await checker.check_ssl_configuration(test_url)
        print(f"      Resultado: {ssl_result['status']} - {ssl_result['message']}")
        if 'risk_explanation' in ssl_result:
            print(f"      Riesgo: {ssl_result['risk_explanation'][:100]}...")

async def test_api_endpoints():
    """Prueba los endpoints de la API"""
    print("\n🧪 Probando endpoints de la API...")
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient() as client:
            # Probar endpoint principal
            print("   🔍 Probando endpoint principal...")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("      ✅ Endpoint principal funcionando")
            else:
                print(f"      ❌ Error en endpoint principal: {response.status_code}")
            
            # Probar endpoint de auditoría
            print("   🔍 Probando endpoint de auditoría...")
            audit_data = {
                "url": "https://httpbin.org",
                "company_name": "Empresa de Prueba"
            }
            
            response = await client.post(
                f"{base_url}/audit",
                json=audit_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ Auditoría completada - Estado: {result.get('overall_status', 'UNKNOWN')}")
            else:
                print(f"      ❌ Error en auditoría: {response.status_code}")
                print(f"      Respuesta: {response.text}")
                
    except httpx.ConnectError:
        print("      ⚠️ No se pudo conectar al servidor. Asegúrate de que esté ejecutándose.")
    except Exception as e:
        print(f"      ❌ Error inesperado: {e}")

def test_configuration():
    """Prueba la configuración del sistema"""
    print("\n🧪 Probando configuración del sistema...")
    
    try:
        from config import Config
        
        print(f"   ✅ Host: {Config.HOST}")
        print(f"   ✅ Puerto: {Config.PORT}")
        print(f"   ✅ Debug: {Config.DEBUG}")
        print(f"   ✅ Timeout: {Config.REQUEST_TIMEOUT}s")
        print(f"   ✅ User Agent: {Config.USER_AGENT}")
        
        headers_config = Config.get_security_headers_config()
        print(f"   ✅ Headers configurados: {len(headers_config)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del WordPress Security Auditor")
    print("=" * 60)
    
    # Probar configuración
    config_ok = test_configuration()
    
    if not config_ok:
        print("❌ Error en configuración. Abortando pruebas.")
        return
    
    # Probar headers de seguridad
    await test_security_headers()
    
    # Probar verificaciones de WordPress
    await test_wordpress_checks()
    
    # Probar API (solo si el servidor está ejecutándose)
    await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("\n💡 Para probar la interfaz web completa:")
    print("   1. Ejecuta: python start.py")
    print("   2. Abre: http://localhost:8000")
    print("   3. Prueba con un sitio WordPress real")

if __name__ == "__main__":
    asyncio.run(main())
