# 📊 Análisis de Costos AWS - ShieldScan

## 🏗️ Arquitectura Propuesta: Proxy Inverso

```
Internet → EC2 Pública (Nginx Proxy) → EC2 Privada (FastAPI + Static)
```

### 💰 Costos Mensuales Estimados

#### **1. Instancia EC2 Pública (Proxy)**
- **Tipo:** `t3.micro` (2 vCPU, 1 GB RAM)
- **Costo:** ~$7.50 USD/mes (0.0104 USD/hora × 730 horas)
- **Función:** Nginx como reverse proxy

#### **2. Instancia EC2 Privada (Aplicación)**
- **Tipo:** `t3.micro` o `t3.small` (2 vCPU, 2 GB RAM)
- **Costo:** 
  - `t3.micro`: ~$7.50 USD/mes
  - `t3.small`: ~$15.00 USD/mes
- **Función:** ShieldScan (FastAPI) + Sitio Web Estático

#### **3. Almacenamiento EBS**
- **Volumen por instancia:** 30 GB (gp3)
- **Costo:** $0.10 USD/GB/mes
- **Total (2 instancias):** ~$6.00 USD/mes

#### **4. Dirección IP Elástica (EIP)**
- **Costo:** **GRATIS** (si está asociada a instancia en ejecución)
- **Nota:** Solo se cobra si la EIP no está asociada ($0.005/hora)

#### **5. Transferencia de Datos**
- **Entrada (Internet → AWS):** GRATIS
- **Salida (AWS → Internet):** 
  - Primeros 100 GB: **GRATIS**
  - Después: $0.09 USD/GB
- **Entre instancias (misma AZ):** GRATIS

#### **6. VPC y Networking**
- **VPC:** GRATIS
- **Subredes:** GRATIS
- **Internet Gateway:** GRATIS
- **Route Tables:** GRATIS

---

## 📈 **TOTAL MENSUAL ESTIMADO**

### Opción 1: t3.micro + t3.micro
```
EC2 Pública (t3.micro):     $7.50
EC2 Privada (t3.micro):     $7.50
EBS (60 GB total):          $6.00
Transferencia de datos:     $0.00 (primeros 100 GB gratis)
─────────────────────────────────
TOTAL:                      $21.00 USD/mes
```

### Opción 2: t3.micro + t3.small (recomendado)
```
EC2 Pública (t3.micro):     $7.50
EC2 Privada (t3.small):     $15.00
EBS (60 GB total):           $6.00
Transferencia de datos:      $0.00
─────────────────────────────────
TOTAL:                      $28.50 USD/mes
```

---

## ⚠️ **PROBLEMA CON TU ARQUITECTURA PROPUESTA**

Tu arquitectura tiene un problema conceptual:

> "Instancia privada que exponga a internet"

**Las instancias privadas NO pueden exponerse directamente a internet** porque:
- No tienen IP pública
- No tienen ruta directa a Internet Gateway
- Están diseñadas para NO ser accesibles desde internet

### ✅ **Solución Correcta:**

La instancia privada **NO expone directamente a internet**. En su lugar:

1. **Internet** → Accede a la instancia pública (IP pública)
2. **Instancia Pública** → Tiene Nginx como reverse proxy
3. **Nginx** → Redirige tráfico a la instancia privada (IP privada)
4. **Instancia Privada** → Procesa y responde
5. **Respuesta** → Vuelve por el mismo camino

---

## 🎯 **ARQUITECTURA RECOMENDADA (MÁS ECONÓMICA)**

### **Opción A: Una Sola Instancia (MÁS BARATA)**

```
Internet → EC2 Pública (FastAPI + Nginx + Static Files)
```

**Costos:**
- 1x `t3.small`: $15.00/mes
- EBS 30 GB: $3.00/mes
- **TOTAL: $18.00 USD/mes** ✅

**Ventajas:**
- ✅ Más simple
- ✅ Más barato
- ✅ Más fácil de mantener
- ✅ Para un MVP personal es suficiente

**Desventajas:**
- ❌ Menos seguro (todo en una instancia)
- ❌ Si cae, cae todo

---

### **Opción B: Dos Instancias con Proxy (TU PROPUESTA)**

```
Internet → EC2 Pública (Nginx) → EC2 Privada (FastAPI + Static)
```

**Costos:**
- 2x `t3.micro`: $15.00/mes
- EBS 60 GB: $6.00/mes
- **TOTAL: $21.00 USD/mes**

**Ventajas:**
- ✅ Más seguro (aplicación aislada)
- ✅ Mejor separación de responsabilidades

**Desventajas:**
- ❌ Más caro
- ❌ Más complejo de configurar
- ❌ Más instancias que mantener

---

## 🔧 **CONFIGURACIÓN TÉCNICA**

### **Instancia Pública (Proxy)**
```nginx
# /etc/nginx/sites-available/shieldscan
server {
    listen 80;
    server_name tu-dominio.com;

    # Redirigir a HTTPS (opcional)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tu-dominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Proxy para FastAPI
    location / {
        proxy_pass http://10.0.1.50:8000;  # IP privada de instancia privada
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Servir archivos estáticos directamente (opcional)
    location /static {
        alias /var/www/static;
    }
}
```

### **Instancia Privada**
- FastAPI corriendo en puerto 8000
- Archivos estáticos en `/var/www/static` o servidos por FastAPI
- Solo accesible desde la instancia pública (Security Group)

---

## 💡 **RECOMENDACIÓN FINAL**

Para un **MVP personal** con **mínimo costo**:

### **Usa Opción A: Una Sola Instancia**
- **Costo:** $18.00 USD/mes
- **Configuración:** Nginx + FastAPI en la misma instancia
- **Seguridad:** Security Groups + Firewall de la instancia

### **Si necesitas más seguridad:**
- **Usa Opción B:** Dos instancias
- **Costo:** $21.00 USD/mes
- **Beneficio:** Aislamiento de la aplicación

---

## 📝 **NOTAS IMPORTANTES**

1. **Free Tier:** Si eres nuevo en AWS, tienes 750 horas/mes gratis de `t2.micro` por 12 meses
   - Podrías tener 1 instancia gratis el primer año
   - **Costo real: $0-3 USD/mes** (solo EBS)

2. **Transferencia de Datos:**
   - Si tu tráfico es bajo (<100 GB/mes), es gratis
   - Para un MVP personal, probablemente no excedas esto

3. **Dominio:**
   - Route 53: $0.50 USD/mes por dominio
   - Certificado SSL: GRATIS con AWS Certificate Manager (ACM)

4. **Backup:**
   - Snapshots EBS: $0.05 USD/GB/mes (opcional)

---

## 🚀 **PRÓXIMOS PASOS**

1. Decidir arquitectura (Opción A o B)
2. Crear VPC y subredes
3. Configurar Security Groups
4. Lanzar instancias
5. Configurar Nginx (si usas Opción B)
6. Desplegar aplicación
7. Configurar dominio y SSL

¿Quieres que te ayude a implementar alguna de estas opciones?


