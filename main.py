from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
import httpx
import asyncio
from datetime import datetime
import json
from typing import Dict, List, Optional
import re
import html
from pathlib import Path

app = FastAPI(title="WordPress Security Auditor", version="1.2.0")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

def sanitize_html(text: str) -> str:
    """Sanitiza texto para prevenir XSS en reportes HTML"""
    if not text:
        return ""
    return html.escape(str(text), quote=True)

class SecurityAuditRequest(BaseModel):
    url: str
    company_name: Optional[str] = None
    auditor_name: Optional[str] = "Equipo de Seguridad y Operaciones"

class SecurityHeaders:
    """Clase para validar headers de seguridad"""
    
    @staticmethod
    def check_security_headers(headers: Dict[str, str]) -> Dict[str, Dict]:
        """Verifica headers de seguridad críticos"""
        results = {}
        
        # Headers críticos de seguridad
        critical_headers = {
            'Strict-Transport-Security': {
                'required': True,
                'description': 'HSTS - Fuerza conexiones HTTPS',
                'recommended': 'max-age=31536000; includeSubDomains; preload'
            },
            'X-Content-Type-Options': {
                'required': True,
                'description': 'Previene MIME type sniffing',
                'recommended': 'nosniff'
            },
            'X-Frame-Options': {
                'required': True,
                'description': 'Previene clickjacking',
                'recommended': 'DENY o SAMEORIGIN'
            },
            'X-XSS-Protection': {
                'required': True,
                'description': 'Protección XSS del navegador',
                'recommended': '1; mode=block'
            },
            'Content-Security-Policy': {
                'required': False,
                'description': 'Política de seguridad de contenido',
                'recommended': 'default-src \'self\''
            },
            'Referrer-Policy': {
                'required': False,
                'description': 'Control de información de referrer',
                'recommended': 'strict-origin-when-cross-origin'
            },
            'Permissions-Policy': {
                'required': False,
                'description': 'Control de permisos de navegador',
                'recommended': 'geolocation=(), microphone=(), camera=()'
            }
        }
        
            # Crear diccionario case-insensitive de headers
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        for header, config in critical_headers.items():
            # Buscar el header en minúsculas
            header_lower = header.lower()
            header_value = headers_lower.get(header_lower, '')
            
            results[header] = {
                'present': bool(header_value),
                'value': header_value,
                'required': config['required'],
                'description': config['description'],
                'recommended': config['recommended'],
                'status': 'PASS' if header_value else ('WARNING' if config['required'] else 'INFO')
            }
        
        return results

class WordPressSecurityChecker:
    """Clase principal para verificar seguridad de WordPress"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0, 
            follow_redirects=True,
            verify=True,  # Verificar certificados SSL
            max_redirects=5
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def check_wp_admin_access(self, base_url: str) -> Dict:
        """Verifica si wp-admin está accesible públicamente"""
        try:
            wp_admin_url = f"{base_url.rstrip('/')}/wp-admin/"
            response = await self.session.get(wp_admin_url)
            
            # Si redirige a login, está bien configurado
            if response.status_code == 302 or response.status_code == 301:
                return {
                    'accessible': False,
                    'status': 'PASS',
                    'message': 'wp-admin redirige correctamente al login',
                    'status_code': response.status_code,
                    'risk_explanation': 'El panel de administración está correctamente protegido y redirige a autenticación.'
                }
            
            # Si devuelve 200, verificar contenido
            elif response.status_code == 200:
                content = response.text.lower()
                if 'login' in content or 'wp-login' in content or 'password' in content:
                    return {
                        'accessible': True,  # Cambiado: mostrar login es una vulnerabilidad
                        'status': 'CRITICAL',  # Cambiado: de PASS a CRITICAL
                        'message': 'VULNERABILIDAD: wp-admin muestra página de login públicamente',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: El panel de login de WordPress es accesible públicamente. Esto permite a atacantes realizar ataques de fuerza bruta, identificar usuarios válidos y explotar vulnerabilidades conocidas en wp-login.php. Se recomienda restringir el acceso mediante IP whitelist, autenticación de dos factores o cambiar la URL de login.'
                    }
                else:
                    return {
                        'accessible': True,
                        'status': 'CRITICAL',
                        'message': 'VULNERABILIDAD: wp-admin parece estar accesible sin autenticación',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: El panel de administración de WordPress es accesible sin autenticación. Esto permite acceso completo al sitio web, modificación de contenido, instalación de plugins maliciosos y robo de datos.'
                    }
            else:
                return {
                    'accessible': False,
                    'status': 'PASS',
                    'message': f'wp-admin no accesible (código: {response.status_code})',
                    'status_code': response.status_code,
                    'risk_explanation': 'El panel de administración está correctamente protegido y no es accesible públicamente.'
                }
                
        except Exception as e:
            return {
                'accessible': None,
                'status': 'ERROR',
                'message': f'Error verificando wp-admin: {str(e)}',
                'status_code': None,
                'risk_explanation': 'No se pudo verificar el estado del panel de administración.'
            }
    
    async def check_xmlrpc_access(self, base_url: str) -> Dict:
        """Verifica si xmlrpc.php está accesible"""
        try:
            xmlrpc_url = f"{base_url.rstrip('/')}/xmlrpc.php"
            response = await self.session.get(xmlrpc_url)
            
            # Cualquier respuesta que no sea 404 indica que el archivo existe
            if response.status_code == 200:
                content = response.text.lower()
                if 'xml' in content and 'rpc' in content:
                    return {
                        'accessible': True,
                        'status': 'CRITICAL',  # Cambiado: de WARNING a CRITICAL
                        'message': 'VULNERABILIDAD: xmlrpc.php está habilitado y accesible',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: XML-RPC está habilitado y accesible. Esto permite ataques de fuerza bruta masivos, ataques DDoS amplificados, y explotación de vulnerabilidades remotas. Los atacantes pueden usar xmlrpc.php para realizar miles de intentos de login por segundo desde una sola petición.',
                        'recommendation': 'Deshabilitar XML-RPC completamente si no es necesario, o restringir su acceso mediante .htaccess o firewall.'
                    }
                else:
                    return {
                        'accessible': True,
                        'status': 'CRITICAL',  # Cambiado: de PASS a CRITICAL
                        'message': 'VULNERABILIDAD: xmlrpc.php responde pero no como esperado',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: El archivo xmlrpc.php existe y responde, lo que indica que XML-RPC está habilitado. Esto representa un vector de ataque significativo.',
                        'recommendation': 'Deshabilitar XML-RPC completamente.'
                    }
            elif response.status_code == 405:  # Method Not Allowed
                return {
                    'accessible': True,  # Cambiado: 405 significa que el archivo existe
                    'status': 'CRITICAL',  # Cambiado: de PASS a CRITICAL
                    'message': 'VULNERABILIDAD: xmlrpc.php accesible (código: 405 - Method Not Allowed)',
                    'status_code': response.status_code,
                    'risk_explanation': 'CRÍTICO: El archivo xmlrpc.php existe y responde con código 405. Aunque solo acepta POST, esto confirma que XML-RPC está habilitado y puede ser explotado para ataques de fuerza bruta y DDoS usando peticiones POST.',
                    'recommendation': 'Deshabilitar XML-RPC completamente mediante .htaccess, plugin de seguridad, o configuración del servidor.'
                }
            elif response.status_code == 404:
                    return {
                        'accessible': False,
                        'status': 'PASS',
                    'message': 'xmlrpc.php no encontrado (código: 404)',
                    'status_code': response.status_code,
                    'risk_explanation': 'CORRECTO: El archivo xmlrpc.php no existe o está correctamente bloqueado. Esto elimina el vector de ataque XML-RPC.',
                    'recommendation': 'Mantener XML-RPC deshabilitado para máxima seguridad.'
                    }
            else:
                return {
                    'accessible': True,  # Cualquier otro código indica que existe
                    'status': 'CRITICAL',  # Cambiado: de PASS a CRITICAL
                    'message': f'VULNERABILIDAD: xmlrpc.php accesible (código: {response.status_code})',
                    'status_code': response.status_code,
                    'risk_explanation': f'CRÍTICO: El archivo xmlrpc.php responde con código {response.status_code}, lo que indica que XML-RPC está habilitado y representa un riesgo de seguridad.',
                    'recommendation': 'Deshabilitar XML-RPC completamente.'
                }
                
        except Exception as e:
            return {
                'accessible': None,
                'status': 'ERROR',
                'message': f'Error verificando xmlrpc.php: {str(e)}',
                'status_code': None,
                'risk_explanation': 'No se pudo verificar el estado de xmlrpc.php.'
            }
    
    async def check_wp_config_exposure(self, base_url: str) -> Dict:
        """Verifica si wp-config.php está expuesto"""
        try:
            config_url = f"{base_url.rstrip('/')}/wp-config.php"
            response = await self.session.get(config_url)
            
            if response.status_code == 200:
                content = response.text.lower()
                if 'db_name' in content or 'db_user' in content or 'db_password' in content:
                    return {
                        'exposed': True,
                        'status': 'CRITICAL',
                        'message': 'VULNERABILIDAD CRÍTICA: wp-config.php expuesto con credenciales de base de datos',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: El archivo wp-config.php está accesible públicamente y contiene credenciales de base de datos (DB_NAME, DB_USER, DB_PASSWORD). Esto permite a atacantes obtener acceso completo a la base de datos, robar información sensible, modificar contenido, y comprometer completamente el sitio web.',
                        'recommendation': 'URGENTE: Mover wp-config.php fuera del directorio web, configurar permisos restrictivos (600), o usar variables de entorno para credenciales.'
                    }
                else:
                    return {
                        'exposed': True,
                        'status': 'CRITICAL',  # Cambiado: de WARNING a CRITICAL
                        'message': 'VULNERABILIDAD: wp-config.php está accesible públicamente',
                        'status_code': response.status_code,
                        'risk_explanation': 'CRÍTICO: El archivo wp-config.php está accesible públicamente. Aunque no contiene credenciales visibles, este archivo puede revelar información sobre la configuración del sitio, rutas del servidor, y otros datos sensibles que pueden ser utilizados por atacantes para planificar ataques más sofisticados.',
                        'recommendation': 'Mover wp-config.php fuera del directorio web público o configurar el servidor para denegar el acceso a este archivo.'
                    }
            else:
                return {
                    'exposed': False,
                    'status': 'PASS',
                    'message': f'wp-config.php no accesible (código: {response.status_code})',
                    'status_code': response.status_code,
                    'risk_explanation': 'CORRECTO: El archivo wp-config.php no es accesible públicamente, lo que protege la configuración sensible del sitio.',
                    'recommendation': 'Mantener wp-config.php protegido y fuera del directorio web público.'
                }
                
        except Exception as e:
            return {
                'exposed': None,
                'status': 'ERROR',
                'message': f'Error verificando wp-config.php: {str(e)}',
                'status_code': None,
                'risk_explanation': 'No se pudo verificar el estado de wp-config.php.'
            }
    
    async def check_directory_listing(self, base_url: str) -> Dict:
        """Verifica si el listado de directorios está habilitado"""
        try:
            # Probar algunos directorios comunes de WordPress
            test_dirs = ['/wp-content/', '/wp-includes/', '/wp-admin/', '/uploads/']
            results = []
            
            for directory in test_dirs:
                test_url = f"{base_url.rstrip('/')}{directory}"
                response = await self.session.get(test_url)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    # Detectar listado de directorios por patrones comunes
                    listing_indicators = [
                        'index of', 'parent directory', 'directory listing',
                        'apache http server', 'apache/2', 'nginx',
                        'last modified', 'size', 'name</th>', '<th>name</th>',
                        '..</a>', 'parent</a>', 'up to parent directory'
                    ]
                    
                    has_listing = any(indicator in content for indicator in listing_indicators)
                    
                    if has_listing:
                        results.append({
                            'directory': directory,
                            'listing_enabled': True,
                            'status': 'CRITICAL',  # Cambiado: de WARNING a CRITICAL
                            'risk_explanation': f'CRÍTICO: El directorio {directory} permite listado de archivos. Esto expone la estructura del sitio, archivos sensibles, y puede revelar información que facilite ataques dirigidos.'
                        })
                    else:
                        results.append({
                            'directory': directory,
                            'listing_enabled': False,
                            'status': 'PASS',
                            'risk_explanation': f'CORRECTO: El directorio {directory} no permite listado de archivos.'
                        })
                else:
                    results.append({
                        'directory': directory,
                        'listing_enabled': False,
                        'status': 'PASS',
                        'risk_explanation': f'CORRECTO: El directorio {directory} no es accesible o está protegido.'
                    })
            
            # Determinar estado general
            any_listing = any(r['listing_enabled'] for r in results)
            return {
                'directory_listing_enabled': any_listing,
                'status': 'CRITICAL' if any_listing else 'PASS',  # Cambiado: de WARNING a CRITICAL
                'message': 'VULNERABILIDAD: Listado de directorios habilitado' if any_listing else 'Listado de directorios deshabilitado',
                'risk_explanation': 'CRÍTICO: El listado de directorios está habilitado en uno o más directorios. Esto permite a atacantes explorar la estructura del sitio, identificar archivos sensibles, y planificar ataques más precisos. Puede exponer archivos de configuración, backups, y otros recursos que no deberían ser públicos.' if any_listing else 'CORRECTO: El listado de directorios está deshabilitado, protegiendo la estructura interna del sitio.',
                'recommendation': 'Deshabilitar el listado de directorios en el servidor web (Apache: Options -Indexes, Nginx: autoindex off) o agregar archivos index.html vacíos en directorios sensibles.' if any_listing else 'Mantener el listado de directorios deshabilitado.',
                'details': results
            }
            
        except Exception as e:
            return {
                'directory_listing_enabled': None,
                'status': 'ERROR',
                'message': f'Error verificando listado de directorios: {str(e)}',
                'risk_explanation': 'No se pudo verificar el estado del listado de directorios.',
                'details': []
            }
    
    async def check_ssl_configuration(self, base_url: str) -> Dict:
        """Verifica configuración SSL"""
        try:
            # Verificar si el sitio usa HTTPS
            if not base_url.startswith('https://'):
                return {
                    'ssl_enabled': False,
                    'status': 'CRITICAL',  # Cambiado: de WARNING a CRITICAL
                    'message': 'VULNERABILIDAD: El sitio no usa HTTPS',
                    'risk_explanation': 'CRÍTICO: El sitio no utiliza HTTPS, lo que significa que toda la comunicación entre el navegador y el servidor es transmitida en texto plano. Esto permite a atacantes interceptar credenciales, cookies de sesión, y cualquier información sensible transmitida.',
                    'recommendation': 'URGENTE: Implementar certificado SSL válido y configurar redirección automática de HTTP a HTTPS.'
                }
            
            # Hacer petición para verificar SSL
            response = await self.session.get(base_url)
            
            # Verificar si la respuesta es exitosa
            if response.status_code == 200:
                return {
                    'ssl_enabled': True,
                    'status': 'PASS',
                    'message': 'SSL está habilitado correctamente',
                    'certificate_valid': True,
                    'risk_explanation': 'CORRECTO: El sitio utiliza HTTPS correctamente, protegiendo la comunicación entre el cliente y el servidor.',
                    'recommendation': 'Mantener el certificado SSL actualizado y configurar HSTS para mayor seguridad.'
                }
            else:
                return {
                    'ssl_enabled': True,
                    'status': 'WARNING',
                    'message': f'SSL habilitado pero respuesta con código {response.status_code}',
                    'certificate_valid': True,
                    'risk_explanation': 'El sitio utiliza HTTPS pero presenta problemas de conectividad o configuración.',
                    'recommendation': 'Verificar la configuración del servidor y el certificado SSL.'
            }
            
        except Exception as e:
            return {
                'ssl_enabled': None,
                'status': 'ERROR',
                'message': f'Error verificando SSL: {str(e)}',
                'certificate_valid': None,
                'risk_explanation': 'No se pudo verificar la configuración SSL del sitio.',
                'recommendation': 'Verificar manualmente la configuración SSL del sitio.'
            }
    
    async def detect_wordpress(self, base_url: str) -> Dict:
        """Detecta si el sitio es WordPress con lógica mejorada"""
        try:
            response = await self.session.get(base_url)
            content = response.text.lower()
            
            wordpress_indicators = {
                'meta_generator': False,
                'wp_json': False,
                'wp_includes': False,
                'wp_content': False,
                'wp_admin': False,
                'wp_login': False,
                'wp_scripts': False,
                'wp_version': False  # NUEVO: Detectar versión específica
            }
            
            # 1. Meta generator (MÁS ESTRICTO)
            import re
            # Patrón más específico para meta generator de WordPress
            meta_pattern = r'<meta[^>]*name=["\']generator["\'][^>]*content=["\']WordPress[^>]*>'
            if re.search(meta_pattern, content, re.IGNORECASE):
                wordpress_indicators['meta_generator'] = True
            
            # 2. WordPress REST API (MÁS ESTRICTO)
            try:
                wp_json_response = await self.session.get(f"{base_url.rstrip('/')}/wp-json/wp/v2/")
                if wp_json_response.status_code == 200:
                    json_content = wp_json_response.text
                    # Verificar que contenga información específica de WordPress
                    if any(keyword in json_content.lower() for keyword in ['wordpress', 'wp-', 'wp_', 'posts', 'pages', 'users']):
                        wordpress_indicators['wp_json'] = True
            except Exception as e:
                # Log error for debugging but don't expose to user
                print(f"Error checking {indicator}: {str(e)}")
                pass
            
            # 3. Directorios WordPress (MÁS ESTRICTO)
            wp_directories = {
                '/wp-includes/': 'wp_includes',
                '/wp-content/': 'wp_content', 
                '/wp-admin/': 'wp_admin'
            }
            
            for directory, indicator in wp_directories.items():
                try:
                    dir_response = await self.session.get(f"{base_url.rstrip('/')}{directory}")
                    # SOLO considerar válido si responde 200 Y contiene contenido típico de WordPress
                    if dir_response.status_code == 200:
                        dir_content = dir_response.text.lower()
                        
                        if directory == '/wp-admin/':
                            # ANÁLISIS ESPECÍFICO PARA WP-ADMIN
                            wp_admin_indicators = [
                                'wordpress' in dir_content,
                                'wp-admin' in dir_content,
                                'wp-login' in dir_content,
                                'wp-submit' in dir_content,
                                'user_login' in dir_content,
                                'user_pass' in dir_content,
                                'wp-login-lost-password' in dir_content,
                                'funciona gracias a wordpress' in dir_content,
                                'acceder' in dir_content and 'wordpress' in dir_content
                            ]
                            # Si detecta al menos 3 indicadores específicos de wp-admin
                            if sum(wp_admin_indicators) >= 3:
                                wordpress_indicators[indicator] = True
                        else:
                            # Verificar contenido específico de WordPress para otros directorios
                            wp_keywords = ['wordpress', 'wp-', 'wp_', 'wp-content', 'wp-includes']
                            if any(keyword in dir_content for keyword in wp_keywords):
                                wordpress_indicators[indicator] = True
                except:
                    pass
            
            # 4. wp-login.php (ANÁLISIS DE CONTENIDO ESPECÍFICO)
            try:
                wp_login_response = await self.session.get(f"{base_url.rstrip('/')}/wp-login.php")
                if wp_login_response.status_code == 200:
                    login_content = wp_login_response.text.lower()
                    # Verificar elementos MUY específicos del login de WordPress
                    wp_login_indicators = [
                        'wordpress' in login_content,
                        'wp-login' in login_content,
                        'wp-submit' in login_content,
                        'user_login' in login_content,
                        'user_pass' in login_content,
                        'rememberme' in login_content,
                        'wp-login-lost-password' in login_content,
                        'funciona gracias a wordpress' in login_content
                    ]
                    # Si detecta al menos 3 indicadores específicos de wp-login
                    if sum(wp_login_indicators) >= 3:
                        wordpress_indicators['wp_login'] = True
            except Exception as e:
                # Log error for debugging but don't expose to user
                print(f"Error checking {indicator}: {str(e)}")
                pass
            
            # 5. Scripts típicos (MÁS ESTRICTO)
            wp_scripts = ['wp-content/themes', 'wp-content/plugins', 'wp-includes/js', 'wp-includes/css']
            for script in wp_scripts:
                if script in content:
                    wordpress_indicators['wp_scripts'] = True
                    break
            
            # 6. NUEVO: Detectar versión de WordPress
            try:
                version_response = await self.session.get(f"{base_url.rstrip('/')}/wp-json/wp/v2/")
                if version_response.status_code == 200:
                    import json
                    try:
                        data = version_response.json()
                        if 'name' in data and 'wordpress' in data['name'].lower():
                            wordpress_indicators['wp_version'] = True
                    except:
                        pass
            except Exception as e:
                # Log error for debugging but don't expose to user
                print(f"Error checking {indicator}: {str(e)}")
                pass
            
            # Calcular confianza con pesos diferentes
            weights = {
                'meta_generator': 4,    # Peso muy alto - muy específico de WordPress
                'wp_version': 4,        # Peso muy alto - muy específico
                'wp_admin': 5,         # Peso MUY ALTO - wp-admin con contenido específico es definitivo
                'wp_login': 5,         # Peso MUY ALTO - wp-login con contenido específico es definitivo
                'wp_json': 2,          # Peso medio - puede ser falso positivo
                'wp_scripts': 2,       # Peso medio - específico de WordPress
                'wp_includes': 1,     # Peso bajo - puede ser coincidencia
                'wp_content': 1       # Peso bajo - puede ser coincidencia
            }
            
            total_weight = sum(weights.values())
            weighted_score = sum(weights[indicator] for indicator, value in wordpress_indicators.items() if value)
            confidence = (weighted_score / total_weight) * 100
            
            # LÓGICA ESPECIAL: Si wp_admin Y wp_login están confirmados, es definitivamente WordPress
            if wordpress_indicators['wp_admin'] and wordpress_indicators['wp_login']:
                is_wordpress = True
                confidence = max(confidence, 85.0)  # Mínimo 85% de confianza
            # LÓGICA ALTERNATIVA: Si wp_login está confirmado Y hay otros indicadores
            elif wordpress_indicators['wp_login'] and (wordpress_indicators['wp_json'] or wordpress_indicators['wp_scripts'] or wordpress_indicators['wp_version']):
                is_wordpress = True
                confidence = max(confidence, 75.0)
            # LÓGICA ALTERNATIVA: Si wp_json está confirmado Y hay otros indicadores
            elif wordpress_indicators['wp_json'] and (wordpress_indicators['wp_scripts'] or wordpress_indicators['wp_version'] or wordpress_indicators['meta_generator']):
                is_wordpress = True
                confidence = max(confidence, 70.0)
            else:
                # UMBRAL NORMAL para otros casos
                is_wordpress = confidence >= 60
            
            # Estado basado en confianza
            if is_wordpress:
                status = 'PASS'
                message = f'WordPress detectado (confianza: {confidence:.1f}%)'
            elif confidence >= 40:
                status = 'WARNING'
                message = f'Posible WordPress (confianza: {confidence:.1f}%)'
            else:
                status = 'INFO'
                message = f'No es WordPress (confianza: {confidence:.1f}%)'
            
            return {
                'is_wordpress': is_wordpress,
                'confidence': confidence,
                'indicators': wordpress_indicators,
                'status': status,
                'message': message,
                'risk_explanation': f'Análisis de detección completado con {confidence:.1f}% de confianza.',
                'recommendation': 'Continuar con auditoría específica según el tipo de sitio detectado.'
            }
            
        except Exception as e:
            return {
                'is_wordpress': False,
                'confidence': 0,
                'indicators': {},
                'status': 'ERROR',
                'message': f'Error detectando WordPress: {str(e)}',
                'risk_explanation': 'No se pudo determinar si el sitio es WordPress.',
                'recommendation': 'Verificar manualmente el tipo de sitio web.'
            }
    
    async def check_general_security(self, base_url: str) -> Dict:
        """Verificaciones de seguridad generales para sitios no-WordPress"""
        try:
            results = {}
            
            # Detectar tecnología del servidor
            response = await self.session.get(base_url)
            server_header = response.headers.get('Server', '')
            
            # Detectar archivos sensibles comunes (excluyendo robots.txt que es normal)
            sensitive_files = [
                '/.env',
                '/config.php',
                '/database.yml',
                '/.git/config',
                '/package.json',
                '/composer.json',
                '/web.config',
                '/.htaccess'
            ]
            
            exposed_files = []
            for file_path in sensitive_files:
                try:
                    file_response = await self.session.get(f"{base_url.rstrip('/')}{file_path}")
                    if file_response.status_code == 200:
                        content = file_response.text.lower()
                        # Verificar que no sea una página de error genérica
                        if not any(error_word in content for error_word in ['404', 'not found', 'error', 'page not found', 'access denied']):
                            # Verificar que el contenido sea realmente sensible
                            if any(sensitive_word in content for sensitive_word in ['password', 'secret', 'key', 'token', 'database', 'config', 'credential']):
                                exposed_files.append(file_path)
                except:
                    pass
            
            # Detectar tecnologías
            technologies = []
            if 'php' in server_header.lower():
                technologies.append('PHP')
            if 'node' in server_header.lower():
                technologies.append('Node.js')
            if 'python' in server_header.lower():
                technologies.append('Python')
            if 'apache' in server_header.lower():
                technologies.append('Apache')
            if 'nginx' in server_header.lower():
                technologies.append('Nginx')
            
            # Detectar frameworks
            frameworks = []
            content = response.text.lower()
            if 'laravel' in content or 'laravel' in server_header.lower():
                frameworks.append('Laravel')
            if 'django' in content or 'django' in server_header.lower():
                frameworks.append('Django')
            if 'express' in content or 'express' in server_header.lower():
                frameworks.append('Express.js')
            if 'react' in content:
                frameworks.append('React')
            if 'vue' in content:
                frameworks.append('Vue.js')
            if 'angular' in content:
                frameworks.append('Angular')
            
            # Determinar estado
            if exposed_files:
                status = 'CRITICAL'
                message = f'Archivos sensibles expuestos: {len(exposed_files)} archivos'
                risk_explanation = f'CRÍTICO: Se detectaron {len(exposed_files)} archivos sensibles expuestos públicamente. Esto puede revelar información confidencial como credenciales, configuraciones de base de datos, y estructura del proyecto.'
                recommendation = 'URGENTE: Proteger o remover archivos sensibles del directorio web público. Configurar el servidor para denegar acceso a archivos de configuración.'
            else:
                status = 'PASS'
                message = 'No se detectaron archivos sensibles expuestos'
                risk_explanation = 'CORRECTO: No se detectaron archivos sensibles expuestos públicamente.'
                recommendation = 'Mantener esta configuración de seguridad.'
            
            return {
                'server_technology': server_header,
                'detected_technologies': technologies,
                'detected_frameworks': frameworks,
                'exposed_sensitive_files': exposed_files,
                'status': status,
                'message': message,
                'risk_explanation': risk_explanation,
                'recommendation': recommendation
            }
            
        except Exception as e:
            return {
                'server_technology': 'Unknown',
                'detected_technologies': [],
                'detected_frameworks': [],
                'exposed_sensitive_files': [],
                'status': 'ERROR',
                'message': f'Error en verificación general: {str(e)}',
                'risk_explanation': 'No se pudo realizar la verificación de seguridad general.',
                'recommendation': 'Verificar manualmente la configuración del sitio.'
            }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Página principal"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WordPress Security Auditor</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0d1117 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%);
                border: 1px solid #333;
                border-radius: 15px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,255,0,0.1);
                padding: 40px;
                max-width: 600px;
                width: 100%;
                position: relative;
            }
            
            .container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #00ff00, #00cc00, #009900);
                border-radius: 15px 15px 0 0;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #00ff00;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 0 0 10px rgba(0,255,0,0.3);
                font-weight: 700;
            }
            
            .header p {
                color: #b0b0b0;
                font-size: 1.1em;
                font-weight: 300;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #00ff00;
                font-weight: 600;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .form-group input {
                width: 100%;
                padding: 15px;
                background: #1a1a1a;
                border: 2px solid #333;
                border-radius: 8px;
                font-size: 16px;
                color: #ffffff;
                transition: all 0.3s ease;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #00ff00;
                box-shadow: 0 0 15px rgba(0,255,0,0.2);
                background: #0f0f0f;
            }
            
            .form-group input::placeholder {
                color: #666;
            }
            
            .btn {
                background: linear-gradient(135deg, #00ff00 0%, #00cc00 50%, #009900 100%);
                color: #000000;
                padding: 15px 30px;
                border: 2px solid #00ff00;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                width: 100%;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 1px;
                position: relative;
                overflow: hidden;
            }
            
            .btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(0,255,0,0.3);
                background: linear-gradient(135deg, #00ff00 0%, #00ff00 50%, #00cc00 100%);
            }
            
            .btn:hover::before {
                left: 100%;
            }
            
            .btn:disabled {
                opacity: 0.4;
                cursor: not-allowed;
                transform: none;
                background: #333;
                border-color: #666;
            }
            
            .loading {
                display: none;
                text-align: center;
                margin-top: 20px;
            }
            
            .spinner {
                border: 4px solid #333;
                border-top: 4px solid #00ff00;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
                box-shadow: 0 0 10px rgba(0,255,0,0.3);
            }
            
            .loading p {
                color: #00ff00;
                margin-top: 15px;
                font-weight: 500;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ ShieldScan 🛡️</h1>
                <p>Sistema automatizado para escaneo de seguridad de sitios web con WordPress</p>
            </div>
            
            <form id="auditForm">
                <div class="form-group">
                    <label for="url">URL del sitio WordPress:</label>
                    <input type="url" id="url" name="url" placeholder="https://ejemplo.com" required>
                </div>
                
                <div class="form-group">
                    <label for="company">Nombre de la empresa (opcional):</label>
                    <input type="text" id="company" name="company" placeholder="Mi Empresa S.A.S.">
                </div>
                
                <button type="submit" class="btn" id="auditBtn">
                    🚀 Iniciar Escaneo de Seguridad
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>🔍 Escaneando vulnerabilidades...</p>
            </div>
        </div>
        
        <script>
            document.getElementById('auditForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const url = document.getElementById('url').value;
                const company = document.getElementById('company').value;
                const btn = document.getElementById('auditBtn');
                const loading = document.getElementById('loading');
                
                btn.disabled = true;
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/audit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            url: url,
                            company_name: company
                        })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        // Redirigir a la página de resultados
                        window.location.href = `/results?data=${encodeURIComponent(JSON.stringify(result))}`;
                    } else {
                        alert('Error al realizar la auditoría. Por favor, verifica la URL e intenta nuevamente.');
                    }
                } catch (error) {
                    alert('Error de conexión. Por favor, intenta nuevamente.');
                } finally {
                    btn.disabled = false;
                    loading.style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    """

def calculate_section_score(checks: list, section_type: str) -> dict:
    """Calcula puntuación para una sección específica"""
    if not checks:
        return {'score': 0, 'status': 'ERROR', 'details': 'No hay verificaciones'}
    
    total_score = 0
    critical_count = 0
    warning_count = 0
    pass_count = 0
    
    for check in checks:
        if isinstance(check, dict) and 'status' in check:
            status = check['status']
            if status == 'CRITICAL':
                critical_count += 1
                total_score += 0  # 0 puntos por crítico
            elif status == 'WARNING':
                warning_count += 1
                total_score += 5  # 5 puntos por warning
            elif status == 'PASS':
                pass_count += 1
                total_score += 10  # 10 puntos por pass
        elif isinstance(check, dict) and 'present' in check:
            # Para headers de seguridad
            if check.get('present', False):
                total_score += 10
                pass_count += 1
            elif check.get('required', False):
                total_score += 0
                critical_count += 1
            else:
                total_score += 5
                warning_count += 1
    
    # Calcular puntuación promedio (0-10) - Solo contar items que contribuyen al score
    contributing_items = critical_count + warning_count + pass_count
    avg_score = total_score / contributing_items if contributing_items > 0 else 0
    
    # Determinar estado de la sección
    if critical_count > 0:
        section_status = 'CRITICAL'
    elif warning_count > 0:
        section_status = 'WARNING'
    else:
        section_status = 'PASS'
    
    return {
        'score': round(avg_score, 1),
        'status': section_status,
        'details': {
            'critical': critical_count,
            'warnings': warning_count,
            'pass': pass_count,
            'total': len(checks)
        }
    }

def calculate_overall_score(section_scores: dict) -> float:
    """Calcula puntuación general basada en secciones"""
    if not section_scores:
        return 0.0
    
    total_score = 0
    section_count = 0
    
    for section, score_data in section_scores.items():
        if isinstance(score_data, dict) and 'score' in score_data:
            total_score += score_data['score']
            section_count += 1
    
    return round(total_score / section_count, 1) if section_count > 0 else 0.0

def get_status_from_score(score: float) -> str:
    """Convierte puntuación numérica a estado"""
    if score >= 7.5:
        return 'PASS'
    elif score >= 5.5:
        return 'WARNING'
    else:
        return 'CRITICAL'

@app.post("/audit")
async def perform_security_audit(request: SecurityAuditRequest):
    """Realiza auditoría completa de seguridad"""
    try:
        # Validar URL
        if not request.url.startswith(('http://', 'https://')):
            request.url = f"https://{request.url}"
        
        async with WordPressSecurityChecker() as checker:
            # Obtener headers de seguridad
            response = await checker.session.get(request.url)
            headers = dict(response.headers)
            
            # DETECCIÓN DE WORDPRESS (NUEVA FUNCIONALIDAD)
            wordpress_detection = await checker.detect_wordpress(request.url)
            
            # Analizar headers de seguridad (siempre se hace)
            security_headers = SecurityHeaders.check_security_headers(headers)
            
            # Compilar resultados base
            audit_results = {
                'url': request.url,
                'company_name': request.company_name or 'Cliente',
                'auditor_name': request.auditor_name,
                'timestamp': datetime.now().isoformat(),
                'wordpress_detection': wordpress_detection,
                'security_headers': security_headers,
                'overall_status': 'PASS'  # Se calculará basado en los resultados
            }
            
            # LÓGICA CONDICIONAL BASADA EN DETECCIÓN DE WORDPRESS
            if wordpress_detection['is_wordpress']:
                # AUDITORÍA WORDPRESS
                tasks = [
                    checker.check_wp_admin_access(request.url),
                    checker.check_xmlrpc_access(request.url),
                    checker.check_wp_config_exposure(request.url),
                    checker.check_directory_listing(request.url),
                    checker.check_ssl_configuration(request.url)
                ]
            
                results = await asyncio.gather(*tasks)
                
                # Agregar resultados específicos de WordPress
                audit_results.update({
                    'site_type': 'WordPress',
                    'wp_admin_access': results[0],
                    'xmlrpc_access': results[1],
                    'wp_config_exposure': results[2],
                    'directory_listing': results[3],
                    'ssl_configuration': results[4]
                })
            else:
                # AUDITORÍA GENERAL - Para sitios no-WordPress
                tasks = [
                    checker.check_general_security(request.url),
                    checker.check_directory_listing(request.url),
                    checker.check_ssl_configuration(request.url)
                ]
                
                results = await asyncio.gather(*tasks)
                
                # Agregar resultados generales
                audit_results.update({
                    'site_type': 'General Web Application',
                    'general_security': results[0],
                    'directory_listing': results[1],
                    'ssl_configuration': results[2]
                })
            
            # NUEVA LÓGICA: Evaluación por secciones (después de completar audit_data)
            section_scores = {}
            
            # 1. Evaluación de Headers de Seguridad
            headers_score = calculate_section_score(list(security_headers.values()), 'headers')
            section_scores['security_headers'] = headers_score
            
            # 2. Evaluación de WordPress (si aplica)
            if audit_results.get('site_type') == 'WordPress':
                # Verificaciones específicas de WordPress
                wp_checks = [
                    audit_results.get('wp_admin_access', {}),
                    audit_results.get('xmlrpc_access', {}),
                    audit_results.get('wp_config_exposure', {})
                ]
                wp_score = calculate_section_score(wp_checks, 'wordpress')
                section_scores['wordpress'] = wp_score
                
                # Verificaciones generales (también aplican para WordPress)
                general_checks = [
                    audit_results.get('directory_listing', {}),
                    audit_results.get('ssl_configuration', {})
                ]
                general_score = calculate_section_score(general_checks, 'general')
                section_scores['general_security'] = general_score
            else:
                # Evaluación General para sitios no-WordPress
                general_checks = [
                    audit_results.get('general_security', {}),
                    audit_results.get('directory_listing', {}),
                    audit_results.get('ssl_configuration', {})
                ]
                general_score = calculate_section_score(general_checks, 'general')
                section_scores['general_security'] = general_score
            
            # 3. Calcular estado general basado en secciones
            overall_score = calculate_overall_score(section_scores)
            audit_results['overall_status'] = get_status_from_score(overall_score)
            audit_results['section_scores'] = section_scores
            audit_results['overall_score'] = overall_score
            
            
            return audit_results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la auditoría: {str(e)}")

@app.get("/results", response_class=HTMLResponse)
async def show_results(data: str):
    """Muestra los resultados de la auditoría"""
    try:
        audit_data = json.loads(data)
        return generate_html_report(audit_data)
    except Exception as e:
        return f"<h1>Error al mostrar resultados: {str(e)}</h1>"

def generate_html_report(audit_data: Dict) -> str:
    """Genera reporte HTML profesional"""
    
    # Determinar colores según el estado (tema oscuro)
    status_colors = {
        'PASS': '#00ff88',      # Verde brillante para PASS
        'WARNING': '#ff8c00',   # Naranja para WARNING
        'CRITICAL': '#ff4444',  # Rojo brillante para CRITICAL
        'ERROR': '#888888'      # Gris para ERROR
    }
    
    overall_color = status_colors.get(audit_data['overall_status'], '#6c757d')
    
    # Generar fecha actual en español
    current_date = datetime.now().strftime('%d de %B de %Y').replace('October', 'Octubre').replace('January', 'Enero').replace('February', 'Febrero').replace('March', 'Marzo').replace('April', 'Abril').replace('May', 'Mayo').replace('June', 'Junio').replace('July', 'Julio').replace('August', 'Agosto').replace('September', 'Septiembre').replace('November', 'Noviembre').replace('December', 'Diciembre')
    
    # Generar HTML del reporte
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Auditoría de Seguridad - {sanitize_html(audit_data['company_name'])}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #e0e0e0;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0d1117 100%);
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%);
                border: 1px solid #333;
                box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,255,0,0.1);
                border-radius: 15px;
            }}
            
            .header {{
                text-align: center;
                padding: 40px 0;
                border-bottom: 3px solid {overall_color};
                margin-bottom: 40px;
            }}
            
            .header h1 {{
                color: #00ff00;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 0 0 15px rgba(0,255,0,0.5);
                font-weight: 700;
            }}
            
            .header .subtitle {{
                color: #b0b0b0;
                font-size: 1.2em;
                margin-bottom: 20px;
                font-weight: 300;
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 12px 25px;
                border-radius: 25px;
                color: #000000;
                font-weight: bold;
                font-size: 1.1em;
                background: {overall_color};
                border: 2px solid {overall_color};
                box-shadow: 0 0 20px {overall_color}40;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .summary {{
                background: linear-gradient(145deg, #1a1a1a 0%, #2a2a2a 100%);
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 40px;
                border-left: 5px solid {overall_color};
                border: 1px solid #333;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            
            .summary h2 {{
                color: #00ff00;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            .section {{
                margin-bottom: 40px;
                padding: 30px;
                border: 1px solid #333;
                border-radius: 10px;
                background: linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            
            .section h3 {{
                color: #00ff00;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #333;
                font-weight: 600;
            }}
            
            .section-score {{
                font-size: 0.8em;
                font-weight: normal;
                color: #00ff88;
                background: rgba(0, 255, 136, 0.1);
                padding: 2px 8px;
                border-radius: 12px;
                border: 1px solid #00ff88;
                margin-left: 10px;
            }}
            
            .check-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                background: linear-gradient(145deg, #1a1a1a 0%, #2a2a2a 100%);
                border: 1px solid #333;
                transition: all 0.3s ease;
            }}
            
            .check-item:hover {{
                background: linear-gradient(145deg, #2a2a2a 0%, #3a3a3a 100%);
                border-color: #555;
            }}
            
            .check-name {{
                font-weight: 600;
                color: #e0e0e0;
            }}
            
            .check-status {{
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9em;
            }}
            
            .status-pass {{
                background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
                color: #000000;
                box-shadow: 0 0 15px rgba(0,255,136,0.3);
                border: 1px solid #00ff88;
            }}
            
            .status-warning {{
                background: linear-gradient(135deg, #ff8c00 0%, #ff6600 100%);
                color: #000000;
                box-shadow: 0 0 15px rgba(255,140,0,0.3);
                border: 1px solid #ff8c00;
            }}
            
            .status-critical {{
                background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
                color: #ffffff;
                box-shadow: 0 0 15px rgba(255,68,68,0.4);
                border: 1px solid #ff4444;
                animation: pulse 2s infinite;
            }}
            
            .status-error {{
                background: linear-gradient(135deg, #888888 0%, #666666 100%);
                color: #ffffff;
                box-shadow: 0 0 10px rgba(136,136,136,0.3);
                border: 1px solid #888888;
            }}
            
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 15px rgba(255,68,68,0.4); }}
                50% {{ box-shadow: 0 0 25px rgba(255,68,68,0.6); }}
                100% {{ box-shadow: 0 0 15px rgba(255,68,68,0.4); }}
            }}
            
            .recommendations {{
                background: linear-gradient(145deg, #1a1a2e 0%, #2a2a3e 100%);
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
                border: 1px solid #333;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            
            .recommendations h4 {{
                color: #00ff00;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            
            .footer {{
                text-align: center;
                padding: 40px 0;
                border-top: 2px solid #333;
                margin-top: 40px;
                color: #b0b0b0;
            }}
            
            .footer .signature {{
                margin-top: 20px;
                font-weight: bold;
                color: #00ff00;
            }}
            
            .print-btn {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #00ff00 0%, #00cc00 100%);
                color: #000000;
                border: 2px solid #00ff00;
                padding: 15px 25px;
                border-radius: 25px;
                cursor: pointer;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(0,255,0,0.3);
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .print-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,255,0,0.4);
                background: linear-gradient(135deg, #00ff00 0%, #00ff00 100%);
            }}
            
            @media print {{
                .print-btn {{
                    display: none;
                }}
                
                body {{
                    background: #0a0a0a !important;
                    color: #e0e0e0 !important;
                }}
                
                .container {{
                    box-shadow: none;
                    margin: 0;
                    padding: 0;
                    background: #1e1e1e !important;
                }}
                
                .section {{
                    background: #2d2d2d !important;
                    border: 1px solid #333 !important;
                }}
                
                .check-item {{
                    background: #1a1a1a !important;
                    border: 1px solid #333 !important;
                }}
            }}
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir PDF</button>
        
        <div class="container">
            <div class="header">
                <h1>🔒 Reporte de Auditoría de Seguridad</h1>
                <div class="subtitle">Sitio: {sanitize_html(audit_data['url'])}</div>
                <div class="subtitle">Cliente: {sanitize_html(audit_data['company_name'])}</div>
                <div class="status-badge">Estado: {sanitize_html(audit_data['overall_status'])}</div>
            </div>
            
            <div class="summary">
                <h2>📋 Resumen Ejecutivo</h2>
                <p>Se ha realizado una auditoría de seguridad completa para el sitio <strong>{sanitize_html(audit_data['url'])}</strong> 
                con el fin de identificar vulnerabilidades y mejorar la postura de seguridad del sitio web. 
                Este análisis incluye la verificación de headers de seguridad, configuración de WordPress, 
                y mejores prácticas de seguridad web.</p>
                
                <p><strong>Fecha de auditoría:</strong> {datetime.fromisoformat(audit_data['timestamp']).strftime('%d de %B de %Y').replace('October', 'Octubre').replace('January', 'Enero').replace('February', 'Febrero').replace('March', 'Marzo').replace('April', 'Abril').replace('May', 'Mayo').replace('June', 'Junio').replace('July', 'Julio').replace('August', 'Agosto').replace('September', 'Septiembre').replace('November', 'Noviembre').replace('December', 'Diciembre')}</p>
                <p><strong>Estado general:</strong> <span style="color: {overall_color}; font-weight: bold;">{audit_data['overall_status']}</span></p>
                <p><strong>Puntuación general:</strong> <span style="color: {overall_color}; font-weight: bold;">{audit_data.get('overall_score', 0)}/10</span></p>
            </div>
    """
    
    # Sección de Detección de WordPress
    if 'wordpress_detection' in audit_data:
        wp_detection = audit_data['wordpress_detection']
        detection_status_class = f"status-{wp_detection['status'].lower()}"
        detection_status_text = wp_detection['status']
        if wp_detection['status'] == 'PASS':
            detection_status_text = '✅ WORDPRESS DETECTADO'
        elif wp_detection['status'] == 'INFO':
            detection_status_text = 'ℹ️ NO WORDPRESS'
        elif wp_detection['status'] == 'ERROR':
            detection_status_text = '❌ ERROR'
        
        html_content += f"""
            <div class="section">
                <h3>🔍 Detección de WordPress</h3>
                <div class="check-item">
                    <div>
                        <div class="check-name">Tipo de Sitio: {wp_detection['message']}</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {wp_detection.get('risk_explanation', '')}
                        </div>
                    </div>
                    <div class="check-status {detection_status_class}">{detection_status_text}</div>
                </div>
        """
        
        # Mostrar indicadores de detección solo si está habilitado en configuración
        from config import Config
        if Config.SHOW_WP_DETECTION_INDICATORS and wp_detection.get('indicators'):
            html_content += """
                        <div class="recommendations">
                            <h4>📊 Indicadores de Detección:</h4>
                            <ul>
                    """
            for indicator, value in wp_detection['indicators'].items():
                status_icon = "✅" if value else "❌"
                indicator_name = indicator.replace('_', ' ').title()
                html_content += f"<li>{status_icon} {indicator_name}: {'Detectado' if value else 'No detectado'}</li>"
            
            html_content += """
                    </ul>
                </div>
        """
        
        html_content += """
            </div>
    """
    
    # Sección de Headers de Seguridad
    headers_score = audit_data.get('section_scores', {}).get('security_headers', {})
    headers_score_value = headers_score.get('score', 0)
    headers_status = headers_score.get('status', 'UNKNOWN')
    
    html_content += f"""
            <div class="section">
                <h3>🛡️ Headers de Seguridad <span class="section-score">({headers_score_value}/10 - {headers_status})</span></h3>
    """
    
    for header, data in audit_data['security_headers'].items():
        status_class = f"status-{data['status'].lower()}"
        html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">{header}</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {data['description']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 3px;">Valor: {data["value"]}</div>' if data['value'] else ''}
                    </div>
                    <div class="check-status {status_class}">{data['status']}</div>
                </div>
    """
    
    # Sección de Verificaciones (condicional según tipo de sitio)
    if audit_data.get('site_type') == 'WordPress':
        # Obtener puntuación de verificaciones WordPress
        wp_score = audit_data.get('section_scores', {}).get('wordpress', {})
        wp_score_value = wp_score.get('score', 0)
        wp_status = wp_score.get('status', 'UNKNOWN')
        
        html_content += f"""
                </div>
                
                <div class="section">
                    <h3>🔧 Verificaciones de WordPress <span class="section-score">({wp_score_value}/10 - {wp_status})</span></h3>
        """
    else:
        # Obtener puntuación de verificaciones generales
        general_score = audit_data.get('section_scores', {}).get('general_security', {})
        general_score_value = general_score.get('score', 0)
        general_status = general_score.get('status', 'UNKNOWN')
        
        html_content += f"""
            </div>
            
            <div class="section">
                <h3>🌐 Verificaciones Generales de Seguridad <span class="section-score">({general_score_value}/10 - {general_status})</span></h3>
        """
    
    # wp-admin access (solo si es WordPress)
    if audit_data.get('site_type') == 'WordPress' and 'wp_admin_access' in audit_data:
        wp_admin = audit_data['wp_admin_access']
        status_class = f"status-{wp_admin['status'].lower()}"
        html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Acceso a wp-admin</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {wp_admin['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {wp_admin.get("risk_explanation", "No disponible")}</div>' if wp_admin.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {wp_admin.get("recommendation", "")}</div>' if wp_admin.get('recommendation') else ''}
                    </div>
                    <div class="check-status {status_class}">{wp_admin['status']}</div>
                </div>
    """
    
    # xmlrpc access
    # xmlrpc.php access (solo si es WordPress)
    if audit_data.get('site_type') == 'WordPress' and 'xmlrpc_access' in audit_data:
        xmlrpc = audit_data['xmlrpc_access']
        status_class = f"status-{xmlrpc['status'].lower()}"
        html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Acceso a xmlrpc.php</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {xmlrpc['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {xmlrpc.get("risk_explanation", "No disponible")}</div>' if xmlrpc.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {xmlrpc.get("recommendation", "")}</div>' if xmlrpc.get('recommendation') else ''}
                    </div>
                    <div class="check-status {status_class}">{xmlrpc['status']}</div>
                </div>
    """
    
    # wp-config exposure
    # wp-config.php exposure (solo si es WordPress)
    if audit_data.get('site_type') == 'WordPress' and 'wp_config_exposure' in audit_data:
        wp_config = audit_data['wp_config_exposure']
        status_class = f"status-{wp_config['status'].lower()}"
        html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Exposición de wp-config.php</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {wp_config['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {wp_config.get("risk_explanation", "No disponible")}</div>' if wp_config.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {wp_config.get("recommendation", "")}</div>' if wp_config.get('recommendation') else ''}
                    </div>
                    <div class="check-status {status_class}">{wp_config['status']}</div>
                </div>
    """
    
    # Directory listing
    dir_listing = audit_data['directory_listing']
    status_class = f"status-{dir_listing['status'].lower()}"
    html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Listado de Directorios</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {dir_listing['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {dir_listing.get("risk_explanation", "No disponible")}</div>' if dir_listing.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {dir_listing.get("recommendation", "")}</div>' if dir_listing.get('recommendation') else ''}
                    </div>
                    <div class="check-status {status_class}">{dir_listing['status']}</div>
                </div>
    """
    
    # SSL configuration
    ssl = audit_data['ssl_configuration']
    status_class = f"status-{ssl['status'].lower()}"
    html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Configuración SSL</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {ssl['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {ssl.get("risk_explanation", "No disponible")}</div>' if ssl.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {ssl.get("recommendation", "")}</div>' if ssl.get('recommendation') else ''}
                    </div>
                    <div class="check-status {status_class}">{ssl['status']}</div>
                </div>
    """
    
    # Verificaciones generales (solo si NO es WordPress)
    if audit_data.get('site_type') != 'WordPress' and 'general_security' in audit_data:
        general_security = audit_data['general_security']
        status_class = f"status-{general_security['status'].lower()}"
        html_content += f"""
                <div class="check-item">
                    <div>
                        <div class="check-name">Archivos Sensibles</div>
                        <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                            {general_security['message']}
                        </div>
                        {f'<div style="font-size: 0.8em; color: #888; margin-top: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid {overall_color};"><strong>Explicación del Riesgo:</strong> {general_security.get("risk_explanation", "No disponible")}</div>' if general_security.get('risk_explanation') else ''}
                        {f'<div style="font-size: 0.8em; color: #007bff; margin-top: 5px;"><strong>Recomendación:</strong> {general_security.get("recommendation", "")}</div>' if general_security.get('recommendation') else ''}
                        {f'<div style="font-size: 0.8em; color: #ff4444; margin-top: 3px;"><strong>Archivos expuestos:</strong> {", ".join(general_security.get("exposed_sensitive_files", []))}</div>' if general_security.get('exposed_sensitive_files') else ''}
                        {f'<div style="font-size: 0.8em; color: #00ff88; margin-top: 3px;"><strong>Tecnologías detectadas:</strong> {", ".join(general_security.get("detected_technologies", []))}</div>' if general_security.get('detected_technologies') else ''}
                        {f'<div style="font-size: 0.8em; color: #00ff88; margin-top: 3px;"><strong>Frameworks detectados:</strong> {", ".join(general_security.get("detected_frameworks", []))}</div>' if general_security.get('detected_frameworks') else ''}
                    </div>
                    <div class="check-status {status_class}">{general_security['status']}</div>
                </div>
    """
    
    # Recomendaciones generales
    html_content += """
            </div>
            
            <div class="section">
                <h3>💡 Recomendaciones Generales</h3>
                <div class="recommendations">
                    <h4>Mejoras de Seguridad Recomendadas:</h4>
                    <ul>
                        <li>Implementar headers de seguridad faltantes (HSTS, CSP, etc.)</li>
                        <li>Configurar correctamente el acceso a wp-admin</li>
                        <li>Deshabilitar XML-RPC si no es necesario</li>
                        <li>Proteger archivos de configuración sensibles</li>
                        <li>Deshabilitar el listado de directorios</li>
                        <li>Implementar certificado SSL válido</li>
                        <li>Mantener WordPress y plugins actualizados</li>
                        <li>Implementar autenticación de dos factores</li>
                        <li>Configurar firewall de aplicaciones web (WAF)</li>
                        <li>Realizar copias de seguridad regulares</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h3>📊 Conclusiones</h3>
                <p>Esta auditoría de seguridad ha identificado varios aspectos importantes para mejorar la seguridad del sitio web. 
                Se recomienda implementar las correcciones sugeridas de manera prioritaria, comenzando por los elementos 
                marcados como CRÍTICOS y WARNING.</p>
                
                <p>Es importante realizar auditorías de seguridad de manera regular y mantener el sitio web actualizado 
                con las últimas versiones de WordPress, temas y plugins.</p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Versión:</strong> 1.1.0</p>
            <p><strong>Ciudad:</strong> Bogotá, Colombia</p>
            <div class="signature">
                <p>ArthurTech - Equipo de Seguridad y Operaciones</p>
            </div>
        </div>
        
        <script>
            // Auto-scroll to top when page loads
            window.onload = function() {
                window.scrollTo(0, 0);
            };
        </script>
    </body>
    </html>
    """
    
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
