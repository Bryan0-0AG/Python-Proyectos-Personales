import socket
import ssl
import pandas as pd
from datetime import datetime, UTC
import json
import pytz

import os
root = os.path.dirname(os.path.abspath(__file__)) # Obtenemos la carpeta actual


# **\\---FUNCIÓN PARA ESCANEAR TLS---//**
def escanear_tls(dominio):
    # Fecha en una zona específica (ej. Bogotá)
    bogota_tz = pytz.timezone("America/Bogota")
    fecha_escaneo = datetime.now(bogota_tz).replace(microsecond=0, tzinfo=None)
    
    versiones = [
        ssl.TLSVersion.TLSv1_3,
        ssl.TLSVersion.TLSv1_2,
        ssl.TLSVersion.TLSv1_1,
        ssl.TLSVersion.TLSv1
    ]
    nil = "---" 
    observaciones = []
    try:
        contexto_ssl = ssl.create_default_context()
        #contexto_ssl.verify_mode = ssl.CERT_NONE
        #contexto_ssl.set_ciphers("ALL:@SECLEVEL=0") # Permitir más compatibilidad
        #contexto_ssl.minimum_version = version
        #contexto_ssl.maximum_version = version

        # Creamos una conexión segura
        with contexto_ssl.wrap_socket(socket.socket(), server_hostname=dominio) as conexion_tls:
            conexion_tls.settimeout(5)
            conexion_tls.connect((dominio, 443)) # Conectamos con puerto general de HTTPS (443)

            # Información básica
            tls_version = conexion_tls.version()
            certificado = conexion_tls.getpeercert()
            cifrado_list = conexion_tls.cipher()

            # Fecha de expiración
            exp_date_str = certificado['notAfter']
            exp_date = datetime.strptime(exp_date_str, "%b %d %H:%M:%S %Y %Z")
            exp_date = exp_date.replace(tzinfo=UTC)
            days_left = (exp_date - datetime.now(UTC)).days

            # Emisor del certificado
            if certificado and "issuer" in certificado:
                emisor = dict(x[0] for x in certificado["issuer"]).get("commonName")            

            puntaje_seguridad = 0

            # Clasificación por versión TLS
            if tls_version in ["TLSv1", "TLSv1.1"]:
                observaciones.append("TLS inseguro (obsoleto)")
                puntaje_seguridad += 10
            elif tls_version == "TLSv1.2":
                puntaje_seguridad += 2  # seguro si cifrado fuerte
            elif tls_version == "TLSv1.3":
                puntaje_seguridad += 0  # totalmente seguro

            # Clasificación por días del certificado
            if days_left < 0:
                observaciones.append("Certificado vencido")
                puntaje_seguridad += 10
            elif days_left <= 7:
                observaciones.append(f"Certificado por vencer ({days_left} días)")
                puntaje_seguridad += 5
            elif days_left <= 30:
                observaciones.append(f"Certificado por vencer ({days_left} días)")
                puntaje_seguridad += 3

            # Clasificación por cifrado
            nombre_cifrado = cifrado_list[0].replace("TLS_", "")
            inseguro = ["RC4", "DES", "3DES", "MD5", "NULL", "EXPORT"]
            moderado = ["AES128", "SHA1"]
            seguro = ["AES256", "CHACHA20", "SHA256"]

            for palabra in inseguro:
                if palabra in nombre_cifrado:
                    observaciones.append(f"Cifrado inseguro: {palabra}")
                    puntaje_seguridad += 5
                    break
            else:
                for palabra in moderado:
                    if palabra in nombre_cifrado:
                        observaciones.append(f"Cifrado moderado: {palabra}")
                        puntaje_seguridad += 3
                        break

            # Clasificación final por puntaje
            if puntaje_seguridad >= 10:
                riesgo = "CRITICO"
            elif 6 <= puntaje_seguridad < 10:
                riesgo = "ALTO"
            elif 3 <= puntaje_seguridad < 6:
                riesgo = "MEDIO"
            else:
                riesgo = "BAJO"
            
            scan_data = {
                "scan_date": fecha_escaneo, 
                "version": tls_version, 
                "emisor": str(emisor), 
                "days_left": int(days_left), 
                "cipher_name": nombre_cifrado, 
                "risk": riesgo, 
                "observaciones": observaciones}
            return scan_data        

    except Exception as e:
        riesgo = "CRITICO"
        if str(e) == "[Errno 11001] getaddrinfo failed" or str(e) == "timed out":
            observaciones.append("No se pudo conectar correctamente al sitio")
        else:
            observaciones.append("No se encontró información válida del certificado.")
        return {
                "scan_date": fecha_escaneo, 
                "version": nil, 
                "emisor": nil, 
                "days_left": None, 
                "cipher_name": nil, 
                "risk": riesgo, 
                "observaciones": observaciones}
    

# **\\---CREACIÓN DE ARCHIVOS---//**
def obtener_archivos():
    rutaCSV = os.path.join(root, f"TLS.SCAN_Dominios.csv")
    if os.path.exists(rutaCSV):
        df = pd.read_csv(rutaCSV)
    else:
        df = pd.DataFrame(columns=["Dominio", "Escaneado en", "Version TLS", "Días restantes", "Emisor de certificado TLS", "Protocolo de cifrado", "Riesgo", "Observaciones"])
        df.to_csv(rutaCSV, index=False)
        
    rutaJSON = os.path.join(root, "Dominios_registrados.json")
    if os.path.exists(rutaJSON): # Aqui almacenamos los dominios registrados en la UI por el usuario
        with open(rutaJSON, "r") as f:
            contenido = f.read().strip()
            if contenido:
                dominios = json.loads(contenido)
            else:
                dominios = []  # ← archivo vacío
    else:
        dominios = []
        with open(rutaJSON, "w") as f:
            json.dump(dominios, f)  # ← lo crea bien desde el inicio                           
    return [df, rutaCSV], [dominios, rutaJSON]


# **\\---MANEJO DE DOMINIOS---//**
def escaneo_y_registro_dominio(dominio):
    archivoCSV, _ = obtener_archivos()
    df, rutaCSV = archivoCSV
    
    # Obtenemos la información del scaneo
    scan_data = escanear_tls(dominio)
    nueva_data = {
        "Dominio": dominio,
        "Escaneado en": scan_data["scan_date"],
        "Version TLS": scan_data["version"],        
        "Días restantes": scan_data["days_left"], 
        "Emisor de certificado TLS": scan_data["emisor"],
        "Protocolo de cifrado": scan_data["cipher_name"],
        "Riesgo": scan_data["risk"],
        "Observaciones": scan_data["observaciones"]
    } 
    
    # Buscamos el dominio en el archivo CSV    
    filtro = df[df["Dominio"] == dominio] 
     # No existe → añadir nueva fila
    if filtro.empty: 
        df = pd.concat([df, pd.DataFrame([nueva_data])], ignore_index=True)
     # Existe → verificar si cambió algo y actualiza   
    else:
        fila_existente = filtro.iloc[0]
        if any(fila_existente[col] != nueva_data[col] for col in nueva_data):
            idx = filtro.index[0]  # primer índice que coincide
            for col in nueva_data:
                df.at[idx, col] = nueva_data[col]
    # Guardamos el CSV
    df.to_csv(rutaCSV, index=False)


# **\\---CONTROL DE ARCHIVOS---//**
def registrar_dominio(nuevo_dominio):
    _, archivoJSON = obtener_archivos()
    dominios, rutaJSON = archivoJSON
    
    if nuevo_dominio not in dominios: # Añadir dominio (sin duplicados)
        dominios.append(nuevo_dominio)
        with open(rutaJSON, "w") as f: # Guardamos los cambios
            json.dump(dominios, f, indent=2)
            escaneo_y_registro_dominio(nuevo_dominio)
            
def eliminar_dominio(dominio):
    # --- Eliminar del CSV ---
    archivoCSV, _ = obtener_archivos()
    df, rutaCSV = archivoCSV
    
    df = df[df["Dominio"] != dominio]  # Filtramos todo menos el dominio
    df.to_csv(rutaCSV, index=False)
    
    # --- Eliminar del JSON ---
    _, archivoJSON = obtener_archivos()
    dominios, rutaJSON = archivoJSON
    
    if dominio in dominios:
        dominios.remove(dominio)
        with open(rutaJSON, "w") as f:
            json.dump(dominios, f, indent=2)                