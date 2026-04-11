#!/usr/bin/env python3
"""
Script para probar la aplicación web completa de ShieldScan
"""

import requests
import json
import time

def test_web_application():
    """Prueba la aplicación web completa"""
    
    base_url = "http://localhost:8000"
    
    print("🌐 SHIELDSCAN - TESTING APLICACIÓN WEB")
    print("=" * 60)
    
    # Sitios de prueba
    test_sites = [
        {
            'url': 'https://wordpress.org',
            'company_name': 'WordPress Foundation',
            'auditor_name': 'ArthurTech Security Team'
        },
        {
            'url': 'https://github.com',
            'company_name': 'GitHub Inc',
            'auditor_name': 'ArthurTech Security Team'
        },
        {
            'url': 'https://gopass.com.co/',
            'company_name': 'GoPass Colombia',
            'auditor_name': 'ArthurTech Security Team'
        }
    ]
    
    for i, site in enumerate(test_sites, 1):
        print(f"\n{'='*20} TEST WEB {i}/{len(test_sites)} {'='*20}")
        print(f"🌐 Probando: {site['url']}")
        print(f"🏢 Empresa: {site['company_name']}")
        print("-" * 60)
        
        try:
            # 1. Verificar que la aplicación esté corriendo
            print("🔍 Verificando aplicación...")
            response = requests.get(f"{base_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ Aplicación funcionando")
            else:
                print(f"❌ Error: {response.status_code}")
                continue
            
            # 2. Realizar auditoría
            print("🔍 Iniciando auditoría...")
            audit_data = {
                'url': site['url'],
                'company_name': site['company_name'],
                'auditor_name': site['auditor_name']
            }
            
            response = requests.post(f"{base_url}/audit", json=audit_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Auditoría completada")
                
                # Mostrar resultados clave
                print(f"📊 Tipo de sitio: {result.get('site_type', 'Unknown')}")
                print(f"🎯 Estado general: {result.get('overall_status', 'Unknown')}")
                
                # Mostrar detección de WordPress
                if 'wordpress_detection' in result:
                    wp_detection = result['wordpress_detection']
                    print(f"🔍 WordPress detectado: {wp_detection.get('is_wordpress', False)}")
                    print(f"📈 Confianza: {wp_detection.get('confidence', 0):.1f}%")
                
                # Mostrar headers de seguridad
                if 'security_headers' in result:
                    headers = result['security_headers']
                    critical_headers = sum(1 for h in headers.values() if h.get('status') == 'WARNING')
                    print(f"🛡️ Headers críticos: {critical_headers}")
                
                # Mostrar verificaciones específicas
                if result.get('site_type') == 'WordPress':
                    print("🔧 Verificaciones WordPress:")
                    for check in ['wp_admin_access', 'xmlrpc_access', 'wp_config_exposure']:
                        if check in result:
                            status = result[check].get('status', 'Unknown')
                            print(f"   - {check}: {status}")
                else:
                    print("🌐 Verificaciones Generales:")
                    if 'general_security' in result:
                        status = result['general_security'].get('status', 'Unknown')
                        print(f"   - Archivos sensibles: {status}")
                
                # 3. Generar reporte HTML
                print("📄 Generando reporte HTML...")
                report_data = json.dumps(result)
                response = requests.get(f"{base_url}/results?data={report_data}", timeout=10)
                
                if response.status_code == 200:
                    print("✅ Reporte HTML generado")
                    print(f"📊 Tamaño del reporte: {len(response.text)} caracteres")
                    
                    # Verificar elementos clave del reporte
                    report_content = response.text
                    if 'Detección de WordPress' in report_content:
                        print("✅ Sección de detección WordPress presente")
                    if 'Headers de Seguridad' in report_content:
                        print("✅ Sección de headers presente")
                    if result.get('site_type') == 'WordPress' and 'Verificaciones de WordPress' in report_content:
                        print("✅ Sección de verificaciones WordPress presente")
                    elif result.get('site_type') != 'WordPress' and 'Verificaciones Generales' in report_content:
                        print("✅ Sección de verificaciones generales presente")
                    
                else:
                    print(f"❌ Error generando reporte: {response.status_code}")
                
            else:
                print(f"❌ Error en auditoría: {response.status_code}")
                print(f"📝 Respuesta: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se puede conectar a la aplicación")
            print("💡 Asegúrate de que la aplicación esté corriendo en http://localhost:8000")
            break
        except requests.exceptions.Timeout:
            print("⏰ Error: Timeout en la solicitud")
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
        
        # Pausa entre tests
        if i < len(test_sites):
            print("\n⏳ Esperando 2 segundos antes del siguiente test...")
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print("🏁 TESTING WEB COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    test_web_application()
