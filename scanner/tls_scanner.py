import socket
import ssl
from datetime import datetime, UTC
from cryptography import x509

from config import ZONA_HORARIA, CIFRADOS_INSEGUROS, CIFRADOS_MODERADOS, CIFRADOS_SEGUROS, PUERTOS_CONEXION


def escanear_tls(dominio: str) -> dict:
    """
    Intenta conectar al dominio en los puertos indicados (por orden).
    El primer puerto que responda se usa para extraer información TLS.
    Si ninguno responde, devuelve error de conexión inmediatamente.
    """
    fecha_escaneo = datetime.now(ZONA_HORARIA).replace(microsecond=0, tzinfo=None)
    nil = "---"
    observaciones = []

    # ── Intentar conexión en cada puerto ─────────────────────────────────────    
    conn_exitosa = None
    puerto_usado = None

    # ── Intentar conexión en cada puerto ─────────────────────────────────────
    for puerto in PUERTOS_CONEXION:
        try:
            # 👇 Contexto permisivo para laboratorio (autofirmados + TLS antiguo)
            contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            contexto.check_hostname = False          # Acepta IPs y autofirmados
            contexto.verify_mode = ssl.CERT_NONE     # No valida cadena de confianza
            contexto.minimum_version = ssl.TLSVersion.TLSv1   # Permite TLS 1.0+
        
            sock = socket.socket()
            sock.settimeout(2)
            conn = contexto.wrap_socket(sock, server_hostname=dominio)
            conn.connect((dominio, puerto))
            conn_exitosa = conn
            puerto_usado = puerto
            break
        except Exception:
            continue

    # ── Si ningún puerto respondió, salir con error ───────────────────────────
    if conn_exitosa is None:
        observaciones.append("No se pudo conectar correctamente al sitio")
        return {
            "scan_date":     fecha_escaneo,
            "port":          None,
            "version":       nil,
            "emisor":        nil,
            "cipher_name":   nil,
            "days_left":     None,
            "risk":          "CRITICO",
            "observaciones": "\n".join(f"* {obs}" for obs in observaciones),
        }
    
    # ── Conectar con puerto exitoso ───────────────────────────
    try:
        with conn_exitosa:
            tls_version  = conn_exitosa.version()
            cifrado_info = conn_exitosa.cipher()

            # 👇 binary=True para obtener el cert aunque sea autofirmado
            cert_der    = conn_exitosa.getpeercert(binary_form=True)
            certificado = conn_exitosa.getpeercert()   # puede estar vacío {}

            # ── Fecha de expiración ───────────────────────────────────────────
            if certificado and certificado.get("notAfter"):
                exp_date  = datetime.strptime(certificado["notAfter"], "%b %d %H:%M:%S %Y %Z")
                exp_date  = exp_date.replace(tzinfo=UTC)
                days_left = (exp_date - datetime.now(UTC)).days
            else:
                # Parsear desde el DER binario con cryptography
                cert_obj  = x509.load_der_x509_certificate(cert_der)
                exp_date  = cert_obj.not_valid_after_utc
                days_left = (exp_date - datetime.now(UTC)).days

            # ── Emisor ────────────────────────────────────────────────────────
            if certificado and certificado.get("issuer"):
                emisor = dict(x[0] for x in certificado["issuer"]).get("commonName", "Desconocido")
            elif cert_der:
                cert_obj = x509.load_der_x509_certificate(cert_der)
                try:
                    emisor = cert_obj.issuer.get_attributes_for_oid(  # 👈 era "misor"
                        x509.NameOID.COMMON_NAME
                    )[0].value
                except IndexError:
                    emisor = "Autofirmado"
            else:
                emisor = "Desconocido"
                
            # ── Puntaje de riesgo ─────────────────────────────────────────────
            puntaje = 0
                
            # ── Protocolo de cifrado ────────────────────────────────────────────────────────
            nombre_cifrado = cifrado_info[0].replace("TLS_", "")
            if any(palabra in nombre_cifrado for palabra in CIFRADOS_INSEGUROS):
                palabra = next(p for p in CIFRADOS_INSEGUROS if p in nombre_cifrado)
                observaciones.append(f"Cifrado inseguro: {palabra}")
                puntaje += 5
            elif any(palabra in nombre_cifrado for palabra in CIFRADOS_MODERADOS):
                palabra = next(p for p in CIFRADOS_MODERADOS if p in nombre_cifrado)
                observaciones.append(f"Cifrado moderado: {palabra}")
                puntaje += 3
            elif any(palabra in nombre_cifrado for palabra in CIFRADOS_SEGUROS):
                palabra = next(p for p in CIFRADOS_SEGUROS if p in nombre_cifrado)
                puntaje -= 1   

            if tls_version in ("TLSv1", "TLSv1.1"):
                observaciones.append("TLSv1.X obsoleto")
                puntaje += 10
            elif tls_version == "TLSv1.2":
                observaciones.append("TLSv1.2 obsoleto ")
                puntaje += 5

            if emisor == "Autofirmado":
                observaciones.append("Certificado autofirmado")
                puntaje += 5

            if days_left < 0:
                observaciones.append("Certificado vencido")
                puntaje += 10
            elif days_left <= 7:
                observaciones.append(f"Certificado vence ({days_left}) días)")
                puntaje += 5
            elif days_left <= 30:
                observaciones.append(f"Certificado vence ({days_left}) días)")
                puntaje += 3

            riesgo = _clasificar_riesgo(puntaje)

            return {
                "scan_date":     fecha_escaneo,
                "port":          puerto_usado,       # 👈 puerto con el que se conectó
                "version":       tls_version,
                "emisor":        str(emisor),
                "days_left":     int(days_left),
                "cipher_name":   nombre_cifrado,
                "risk":          riesgo,
                "observaciones": "\n".join(f"* {obs}" for obs in observaciones),
            }

    except Exception as e:
        mensaje = (
            "No se pudo conectar correctamente al sitio"
            if str(e) in ("[Errno 11001] getaddrinfo failed", "timed out")
            else "No se encontró información válida del certificado."
        )
        observaciones.append(mensaje)
        return {
            "scan_date":     fecha_escaneo,
            "port":          puerto_usado,
            "version":       nil,
            "emisor":        nil,
            "days_left":     None,
            "cipher_name":   nil,
            "risk":          "CRITICO",
            "observaciones": "\n".join(f"* {obs}" for obs in observaciones),
        }

# ── Helpers ────────────────────────────────────────────────────────────────────
def _clasificar_riesgo(puntaje: int) -> str:
    if puntaje >= 10:
        return "CRITICO"
    if puntaje >= 6:
        return "ALTO"
    if puntaje >= 3:
        return "MEDIO"
    return "BAJO"