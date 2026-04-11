#!/usr/bin/env python3
"""
Script de testing completo para ShieldScan
Prueba toda la funcionalidad: detección WordPress + auditoría completa
"""

import asyncio
import sys
import os
import json

# Agregar el directorio actual al path para importar main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import WordPressSecurityChecker, SecurityHeaders

async def test_complete_audit():
    """Prueba completa del sistema de auditoría"""
    
    # Sitios de prueba diversos
    test_sites = [
        {
            'url': 'https://wordpress.org',
            'expected_wordpress': True,
            'name': 'WordPress.org (oficial)',
            'category': 'WordPress'
        },
        {
            'url': 'https://github.com',
            'expected_wordpress': False,
            'name': 'GitHub (no WordPress)',
            'category': 'General Web'
        },
        {
            'url': 'https://www.google.com',
            'expected_wordpress': False,
            'name': 'Google (no WordPress)',
            'category': 'General Web'
        },
        {
            'url': 'https://gopass.com.co/',
            'expected_wordpress': False,
            'name': 'GoPass (no WordPress)',
            'category': 'General Web'
        }
    ]
    
    print("🔍 SHIELDSCAN - TESTING COMPLETO")
    print("=" * 80)
    
    async with WordPressSecurityChecker() as checker:
        for i, site in enumerate(test_sites, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_sites)} {'='*20}")
            print(f"🌐 Sitio: {site['name']}")
            print(f"🔗 URL: {site['url']}")
            print(f"📂 Categoría: {site['category']}")
            print("-" * 60)
            
            try:
                # 1. DETECCIÓN DE WORDPRESS
                print("🔍 FASE 1: Detección de WordPress")
                wp_detection = await checker.detect_wordpress(site['url'])
                
                print(f"   Resultado: {wp_detection['message']}")
                print(f"   Confianza: {wp_detection['confidence']:.1f}%")
                print(f"   Es WordPress: {wp_detection['is_wordpress']}")
                print(f"   Estado: {wp_detection['status']}")
                
                # Verificar predicción
                prediction_correct = wp_detection['is_wordpress'] == site['expected_wordpress']
                status_icon = "✅" if prediction_correct else "❌"
                print(f"   {status_icon} Predicción: {'CORRECTA' if prediction_correct else 'INCORRECTA'}")
                
                # Mostrar indicadores
                if wp_detection.get('indicators'):
                    print("   📊 Indicadores:")
                    for indicator, value in wp_detection['indicators'].items():
                        icon = "✅" if value else "❌"
                        print(f"      {icon} {indicator}: {value}")
                
                # 2. HEADERS DE SEGURIDAD
                print("\n🛡️ FASE 2: Headers de Seguridad")
                response = await checker.session.get(site['url'])
                headers = dict(response.headers)
                security_headers = SecurityHeaders.check_security_headers(headers)
                
                headers_status = {}
                for header, data in security_headers.items():
                    headers_status[header] = data['status']
                    status_icon = "✅" if data['status'] == 'PASS' else "⚠️" if data['status'] == 'WARNING' else "❌"
                    print(f"   {status_icon} {header}: {data['status']}")
                
                # 3. VERIFICACIONES ESPECÍFICAS
                print(f"\n🔧 FASE 3: Verificaciones {'WordPress' if wp_detection['is_wordpress'] else 'Generales'}")
                
                if wp_detection['is_wordpress']:
                    # Verificaciones WordPress
                    tasks = [
                        checker.check_wp_admin_access(site['url']),
                        checker.check_xmlrpc_access(site['url']),
                        checker.check_wp_config_exposure(site['url']),
                        checker.check_directory_listing(site['url']),
                        checker.check_ssl_configuration(site['url'])
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    check_names = ['wp-admin', 'xmlrpc.php', 'wp-config.php', 'Directory Listing', 'SSL']
                    
                    for check_name, result in zip(check_names, results):
                        status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARNING' else "❌"
                        print(f"   {status_icon} {check_name}: {result['status']}")
                        print(f"      📝 {result['message']}")
                
                else:
                    # Verificaciones Generales
                    tasks = [
                        checker.check_general_security(site['url']),
                        checker.check_directory_listing(site['url']),
                        checker.check_ssl_configuration(site['url'])
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    check_names = ['Archivos Sensibles', 'Directory Listing', 'SSL']
                    
                    for check_name, result in zip(check_names, results):
                        status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARNING' else "❌"
                        print(f"   {status_icon} {check_name}: {result['status']}")
                        print(f"      📝 {result['message']}")
                        
                        # Mostrar detalles adicionales para verificaciones generales
                        if check_name == 'Archivos Sensibles' and result.get('exposed_sensitive_files'):
                            print(f"      🚨 Archivos expuestos: {', '.join(result['exposed_sensitive_files'])}")
                        if result.get('detected_technologies'):
                            print(f"      🔧 Tecnologías: {', '.join(result['detected_technologies'])}")
                        if result.get('detected_frameworks'):
                            print(f"      🏗️ Frameworks: {', '.join(result['detected_frameworks'])}")
                
                # 4. RESUMEN DEL TEST
                print(f"\n📊 RESUMEN DEL TEST")
                print(f"   🎯 Detección WordPress: {'✅ CORRECTA' if prediction_correct else '❌ INCORRECTA'}")
                
                # Contar headers críticos
                critical_headers = sum(1 for status in headers_status.values() if status == 'WARNING')
                print(f"   🛡️ Headers críticos: {critical_headers}")
                
                # Contar verificaciones críticas
                critical_checks = sum(1 for result in results if result['status'] == 'CRITICAL')
                warning_checks = sum(1 for result in results if result['status'] == 'WARNING')
                print(f"   🔍 Verificaciones críticas: {critical_checks}")
                print(f"   ⚠️ Verificaciones con advertencias: {warning_checks}")
                
                # Estado general
                if critical_checks > 0:
                    overall_status = "🔴 CRÍTICO"
                elif warning_checks > 0 or critical_headers > 0:
                    overall_status = "🟡 ADVERTENCIA"
                else:
                    overall_status = "🟢 SEGURO"
                
                print(f"   🎯 Estado general: {overall_status}")
                
            except Exception as e:
                print(f"❌ Error en el test: {str(e)}")
    
    print(f"\n{'='*80}")
    print("🏁 TESTING COMPLETO FINALIZADO")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_complete_audit())
