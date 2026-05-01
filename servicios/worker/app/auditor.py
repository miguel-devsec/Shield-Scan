"""
Core security audit logic — synchronous version for Celery worker.
Adapted from the original FastAPI monolith (main.py).
"""
import re
import html
from typing import Dict, List
import httpx


def sanitize(text: str) -> str:
    return html.escape(str(text), quote=True) if text else ""


class SecurityAuditor:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            verify=True,
            max_redirects=5,
        )

    def close(self):
        self.client.close()

    # ------------------------------------------------------------------ #
    # Security headers                                                     #
    # ------------------------------------------------------------------ #
    def check_security_headers(self, headers: Dict[str, str]) -> Dict:
        critical_headers = {
            "Strict-Transport-Security": {
                "required": True,
                "description": "HSTS - Fuerza conexiones HTTPS",
                "recommended": "max-age=31536000; includeSubDomains; preload",
            },
            "X-Content-Type-Options": {
                "required": True,
                "description": "Previene MIME type sniffing",
                "recommended": "nosniff",
            },
            "X-Frame-Options": {
                "required": True,
                "description": "Previene clickjacking",
                "recommended": "DENY o SAMEORIGIN",
            },
            "X-XSS-Protection": {
                "required": True,
                "description": "Protección XSS del navegador",
                "recommended": "1; mode=block",
            },
            "Content-Security-Policy": {
                "required": False,
                "description": "Política de seguridad de contenido",
                "recommended": "default-src 'self'",
            },
            "Referrer-Policy": {
                "required": False,
                "description": "Control de información de referrer",
                "recommended": "strict-origin-when-cross-origin",
            },
            "Permissions-Policy": {
                "required": False,
                "description": "Control de permisos de navegador",
                "recommended": "geolocation=(), microphone=(), camera=()",
            },
        }

        headers_lower = {k.lower(): v for k, v in headers.items()}
        results = {}
        for header, cfg in critical_headers.items():
            value = headers_lower.get(header.lower(), "")
            results[header] = {
                "present": bool(value),
                "value": value,
                "required": cfg["required"],
                "description": cfg["description"],
                "recommended": cfg["recommended"],
                "status": "PASS" if value else ("WARNING" if cfg["required"] else "INFO"),
            }
        return results

    # ------------------------------------------------------------------ #
    # WordPress detection                                                  #
    # ------------------------------------------------------------------ #
    def detect_wordpress(self) -> Dict:
        try:
            response = self.client.get(self.base_url)
            content = response.text.lower()

            indicators = {
                "meta_generator": bool(
                    re.search(
                        r"<meta[^>]*name=['\"]generator['\"][^>]*content=['\"]WordPress",
                        content,
                        re.IGNORECASE,
                    )
                ),
                "wp_scripts": any(
                    kw in content
                    for kw in ["wp-content/themes", "wp-content/plugins", "wp-includes/js"]
                ),
                "wp_json": False,
                "wp_login": False,
            }

            try:
                r = self.client.get(f"{self.base_url}/wp-json/wp/v2/")
                if r.status_code == 200 and any(
                    kw in r.text.lower() for kw in ["wordpress", "wp-", "posts"]
                ):
                    indicators["wp_json"] = True
            except Exception:
                pass

            try:
                r = self.client.get(f"{self.base_url}/wp-login.php")
                if r.status_code == 200:
                    lc = r.text.lower()
                    hits = sum(
                        kw in lc
                        for kw in ["wordpress", "wp-login", "user_login", "user_pass", "rememberme"]
                    )
                    indicators["wp_login"] = hits >= 3
            except Exception:
                pass

            weights = {"meta_generator": 4, "wp_scripts": 2, "wp_json": 2, "wp_login": 5}
            total = sum(weights.values())
            score = sum(weights[k] for k, v in indicators.items() if v)
            confidence = (score / total) * 100
            is_wp = confidence >= 50 or indicators["wp_login"]

            return {
                "is_wordpress": is_wp,
                "confidence": round(confidence, 1),
                "indicators": indicators,
                "status": "PASS" if is_wp else "INFO",
                "message": f"WordPress detectado (confianza: {confidence:.1f}%)"
                if is_wp
                else f"No es WordPress (confianza: {confidence:.1f}%)",
            }
        except Exception as exc:
            return {
                "is_wordpress": False,
                "confidence": 0,
                "indicators": {},
                "status": "ERROR",
                "message": f"Error detectando WordPress: {exc}",
            }

    # ------------------------------------------------------------------ #
    # WordPress-specific checks                                            #
    # ------------------------------------------------------------------ #
    def check_wp_admin(self) -> Dict:
        try:
            r = self.client.get(f"{self.base_url}/wp-admin/")
            if r.status_code in (301, 302):
                return {"status": "PASS", "message": "wp-admin redirige correctamente al login"}
            if r.status_code == 200:
                lc = r.text.lower()
                if any(kw in lc for kw in ["login", "wp-login", "password"]):
                    return {
                        "status": "CRITICAL",
                        "message": "VULNERABILIDAD: wp-admin muestra página de login públicamente",
                        "risk_explanation": "El panel de login es accesible públicamente, permitiendo ataques de fuerza bruta.",
                        "recommendation": "Restringir acceso mediante IP whitelist o cambiar la URL de login.",
                    }
            return {"status": "PASS", "message": f"wp-admin no accesible (código: {r.status_code})"}
        except Exception as exc:
            return {"status": "ERROR", "message": f"Error verificando wp-admin: {exc}"}

    def check_xmlrpc(self) -> Dict:
        try:
            r = self.client.get(f"{self.base_url}/xmlrpc.php")
            if r.status_code == 404:
                return {"status": "PASS", "message": "xmlrpc.php no encontrado (código: 404)"}
            return {
                "status": "CRITICAL",
                "message": f"VULNERABILIDAD: xmlrpc.php accesible (código: {r.status_code})",
                "risk_explanation": "XML-RPC habilitado permite ataques de fuerza bruta masivos y DDoS amplificados.",
                "recommendation": "Deshabilitar XML-RPC mediante .htaccess o plugin de seguridad.",
            }
        except Exception as exc:
            return {"status": "ERROR", "message": f"Error verificando xmlrpc.php: {exc}"}

    def check_wp_config(self) -> Dict:
        try:
            r = self.client.get(f"{self.base_url}/wp-config.php")
            if r.status_code == 200:
                return {
                    "status": "CRITICAL",
                    "message": "VULNERABILIDAD: wp-config.php está accesible públicamente",
                    "risk_explanation": "El archivo de configuración puede exponer credenciales de la base de datos.",
                    "recommendation": "Mover wp-config.php fuera del directorio web público.",
                }
            return {"status": "PASS", "message": f"wp-config.php no accesible (código: {r.status_code})"}
        except Exception as exc:
            return {"status": "ERROR", "message": f"Error verificando wp-config.php: {exc}"}

    # ------------------------------------------------------------------ #
    # Common checks                                                        #
    # ------------------------------------------------------------------ #
    def check_directory_listing(self) -> Dict:
        test_dirs = ["/wp-content/", "/wp-includes/", "/uploads/", "/static/"]
        listing_indicators = [
            "index of", "parent directory", "directory listing",
            "last modified", "name</th>", "..</a>",
        ]
        exposed = []
        for directory in test_dirs:
            try:
                r = self.client.get(f"{self.base_url}{directory}")
                if r.status_code == 200:
                    lc = r.text.lower()
                    if any(ind in lc for ind in listing_indicators):
                        exposed.append(directory)
            except Exception:
                pass

        if exposed:
            return {
                "status": "CRITICAL",
                "message": f"VULNERABILIDAD: Listado de directorios habilitado en: {', '.join(exposed)}",
                "risk_explanation": "El listado de directorios expone la estructura del sitio a atacantes.",
                "recommendation": "Deshabilitar listado (Apache: Options -Indexes, Nginx: autoindex off).",
                "exposed_directories": exposed,
            }
        return {
            "status": "PASS",
            "message": "Listado de directorios deshabilitado",
            "exposed_directories": [],
        }

    def check_ssl(self) -> Dict:
        if not self.base_url.startswith("https://"):
            return {
                "status": "CRITICAL",
                "message": "VULNERABILIDAD: El sitio no usa HTTPS",
                "risk_explanation": "Comunicación en texto plano permite interceptar credenciales y sesiones.",
                "recommendation": "Implementar certificado SSL y redirigir HTTP → HTTPS.",
            }
        try:
            r = self.client.get(self.base_url)
            if r.status_code < 400:
                return {"status": "PASS", "message": "SSL habilitado correctamente"}
            return {"status": "WARNING", "message": f"SSL habilitado pero respuesta {r.status_code}"}
        except Exception as exc:
            return {"status": "ERROR", "message": f"Error verificando SSL: {exc}"}

    def check_sensitive_files(self) -> Dict:
        sensitive = ["/.env", "/config.php", "/.git/config", "/web.config", "/.htaccess"]
        exposed = []
        for path in sensitive:
            try:
                r = self.client.get(f"{self.base_url}{path}")
                if r.status_code == 200:
                    lc = r.text.lower()
                    if any(kw in lc for kw in ["password", "secret", "key", "token", "database"]):
                        exposed.append(path)
            except Exception:
                pass

        if exposed:
            return {
                "status": "CRITICAL",
                "message": f"Archivos sensibles expuestos: {', '.join(exposed)}",
                "risk_explanation": "Archivos de configuración con credenciales expuestos públicamente.",
                "recommendation": "Remover o proteger archivos de configuración del directorio web.",
                "exposed_files": exposed,
            }
        return {
            "status": "PASS",
            "message": "No se detectaron archivos sensibles expuestos",
            "exposed_files": [],
        }

    # ------------------------------------------------------------------ #
    # Full audit                                                           #
    # ------------------------------------------------------------------ #
    def run(self) -> Dict:
        from datetime import datetime

        try:
            response = self.client.get(self.base_url)
            headers = dict(response.headers)
        except Exception as exc:
            return {"error": str(exc), "status": "ERROR"}

        security_headers = self.check_security_headers(headers)
        wp_detection = self.detect_wordpress()
        ssl = self.check_ssl()
        dir_listing = self.check_directory_listing()

        result = {
            "url": self.base_url,
            "timestamp": datetime.utcnow().isoformat(),
            "wordpress_detection": wp_detection,
            "security_headers": security_headers,
            "ssl_configuration": ssl,
            "directory_listing": dir_listing,
        }

        if wp_detection["is_wordpress"]:
            result["site_type"] = "WordPress"
            result["wp_admin_access"] = self.check_wp_admin()
            result["xmlrpc_access"] = self.check_xmlrpc()
            result["wp_config_exposure"] = self.check_wp_config()
        else:
            result["site_type"] = "General Web Application"
            result["sensitive_files"] = self.check_sensitive_files()

        # Calculate overall status
        all_statuses = self._collect_statuses(result)
        if "CRITICAL" in all_statuses:
            result["overall_status"] = "CRITICAL"
        elif "WARNING" in all_statuses:
            result["overall_status"] = "WARNING"
        else:
            result["overall_status"] = "PASS"

        return result

    def _collect_statuses(self, data: Dict) -> List[str]:
        statuses = []
        skip_keys = {"url", "timestamp", "site_type", "overall_status"}
        for key, value in data.items():
            if key in skip_keys:
                continue
            if isinstance(value, dict):
                if "status" in value:
                    statuses.append(value["status"])
                statuses.extend(self._collect_statuses(value))
        return statuses
