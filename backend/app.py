import streamlit as st
import os
import sqlite3
import pyotp
import qrcode
import math
from datetime import datetime
from io import BytesIO
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

# 1. CONFIGURACIÓN E IMPORTACIONES
st.set_page_config(page_title="Zero-State Protection", page_icon="🔐", layout="wide")
load_dotenv()

# Asumiendo que estos módulos están en tu directorio local
from security import derivar_llave_maestra 
from database import (
    inicializar_db, guardar_config_inicial, 
    db_guardar_credencial, db_obtener_secreto_completo, db_borrar_credencial
) 
from kyber_py.ml_kem import ML_KEM_768 
from quantum_random import generacion_contraseñas # Se usa solo para passwords de cuentas

inicializar_db()

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "generating" not in st.session_state:
    st.session_state.generating = False

# ======================== LÓGICA DE SEGURIDAD ========================

def es_password_segura(password):
    if len(password) < 12: return False, "⚠️ Mínimo 12 caracteres."
    if not any(c.isupper() for c in password): return False, "⚠️ Falta una MAYÚSCULA."
    if not any(c.islower() for c in password): return False, "⚠️ Falta un minúscula."
    if not any(c.isdigit() for c in password): return False, "⚠️ Falta un número."
    if not any(c in "!@#$%^&*" for c in password): return False, "⚠️ Falta un símbolo (!@#$%^&*)."
    return True, ""

# ======================== PANTALLA DE ACCESO ========================

def pantalla_login():
    st.title("🔐 Acceso a la Bóveda Post-Cuántica")
    
    conn = sqlite3.connect("vault.db")
    config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk, totp_secret FROM configuracion WHERE id=1").fetchone()
    conn.close()

    # --- FLUJO A: MOSTRAR KIT TRAS CREACIÓN ---
    if st.session_state.get("setup_complete"):
        st.success("🎉 ¡Bóveda Sellada con éxito!")
        st.info("Descarga tu identidad y escanea el QR. Son tus únicos métodos de recuperación.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Identidad Digital")
            st.download_button(
                "💾 Descargar recovery_identity.bin", 
                data=st.session_state.recovery_bin, 
                file_name="recovery_identity.bin"
            )
        with c2:
            st.subheader("2. Google Authenticator")
            qr_img = qrcode.make(st.session_state.totp_uri)
            buf = BytesIO()
            qr_img.save(buf)
            st.image(buf.getvalue(), caption="Escanea este código QR")
        
        if st.button("🚀 Entrar a la Bóveda"):
            del st.session_state.setup_complete
            st.session_state.unlocked = True
            st.rerun()
        return

    # --- FLUJO B: REGISTRO INICIAL ---
    if not config:
        st.header("✨ Configuración Inicial")
        m_pass = st.text_input("Define tu Master Password", type="password")

        if st.button("🚀 Crear Bóveda"):
            valida, msg = es_password_segura(m_pass)
            if valida:
                with st.spinner("Generando Identidad PQC..."):
                    try:
                        # Generación de llaves Kyber
                        ek, dk = ML_KEM_768.keygen()
                        
                        # Cifrado de la llave privada (DK) con la Master Password
                        salt = os.urandom(16)
                        m_key = derivar_llave_maestra(m_pass, salt)
                        n_dk = os.urandom(12)
                        dk_c = AESGCM(m_key).encrypt(n_dk, dk, None)
                        
                        # Generación del Kit de Rescate (Binario cifrado con el Secreto TOTP)
                        totp_sec = pyotp.random_base32()
                        r_salt = os.urandom(16)
                        # Usamos el secreto TOTP como "llave" para el binario de rescate
                        r_m_key = derivar_llave_maestra(totp_sec, r_salt)
                        r_n = os.urandom(12)
                        r_blob = AESGCM(r_m_key).encrypt(r_n, dk, None)
                        
                        guardar_config_inicial(ek, dk_c, salt, n_dk, totp_sec)
                        
                        st.session_state.recovery_bin = r_salt + r_n + r_blob
                        st.session_state.totp_uri = pyotp.totp.TOTP(totp_sec).provisioning_uri(
                            name="Usuario", issuer_name="ZS-Protection"
                        )
                        st.session_state.setup_complete = True
                        st.session_state.dk, st.session_state.ek = dk, ek
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en la creación: {e}")
            else:
                st.error(msg)

    # --- FLUJO C: LOGIN O RESCATE ---
    else:
        with st.form("login_form"):
            pwd_input = st.text_input("Master Password", type="password")
            if st.form_submit_button("Desbloquear"):
                if pwd_input:
                    # Re-derivación para validar acceso
                    ek_db, dk_c_db, salt_db, n_db, _ = config
                    m_key = derivar_llave_maestra(pwd_input, salt_db)
                    try:
                        decrypted_dk = AESGCM(m_key).decrypt(n_db, dk_c_db, None)
                        st.session_state.dk = decrypted_dk
                        st.session_state.ek = ek_db
                        st.session_state.unlocked = True
                        st.rerun()
                    except:
                        st.error("❌ Contraseña incorrecta.")
                else:
                    st.warning("Introduce tu contraseña.")

        with st.expander("🆘 Rescate de Emergencia"):
            st.write("Sube tu archivo .bin y usa tu código 2FA para resetear la contraseña.")
            file = st.file_uploader("Cargar recovery_identity.bin", type=["bin"])
            otp_in = st.text_input("Código 2FA (6 dígitos)", max_chars=6)
            new_p = st.text_input("Nueva Master Password", type="password")
            
            if st.button("🔓 Restaurar Acceso"):
                if file and otp_in and new_p:
                    totp_secret_db = config[4]
                    if pyotp.TOTP(totp_secret_db).verify(otp_in):
                        try:
                            data = file.read()
                            rs, rn, rb = data[:16], data[16:28], data[28:]
                            # Descifrar binario con el secreto TOTP
                            rmk = derivar_llave_maestra(totp_secret_db, rs)
                            dk_orig = AESGCM(rmk).decrypt(rn, rb, None)
                            
                            # Cifrar con la nueva contraseña
                            ns, nn = os.urandom(16), os.urandom(12)
                            nmk = derivar_llave_maestra(new_p, ns)
                            ndkc = AESGCM(nmk).encrypt(nn, dk_orig, None)
                            
                            conn = sqlite3.connect("vault.db")
                            conn.execute("UPDATE configuracion SET dk_cifrada=?, salt=?, nonce_dk=? WHERE id=1", (ndkc, ns, nn))
                            conn.commit()
                            conn.close()
                            st.success("✅ Acceso restaurado. Inicia sesión con tu nueva contraseña.")
                        except:
                            st.error("❌ El archivo binario es inválido o está dañado.")
                    else:
                        st.error("❌ Código 2FA incorrecto.")
                else:
                    st.warning("Completa todos los campos.")

if not st.session_state.unlocked:
    pantalla_login()
    st.stop()

# ======================== INTERFAZ PRINCIPAL (DESBLOQUEADA) ========================

st.sidebar.title("🛡️ PQC Vault")
opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "➕ Generar", "📋 Mi Cofre"])

if st.sidebar.button("🔒 Cerrar Bóveda"):
    st.session_state.unlocked = False
    st.rerun()

if opcion == "🏠 Inicio":
    st.title("🚀 Bóveda Activa")
    st.success("Identidad verificada. Las llaves privadas están protegidas en RAM.")

elif opcion == "➕ Generar":
    st.title("➕ Nueva Credencial")
    serv = st.text_input("Servicio (ej. Gmail, Amazon)")
    long = st.slider("Longitud", 12, 32, 20)
    
    if st.button("Generar con IBM Quantum"):
        if serv:
            st.session_state.generating = True
            with st.spinner("⏳ Generando entropía cuántica..."):
                try:
                    pass_q = generacion_contraseñas(long)
                    # Encapsulación Kyber
                    sk, ct = ML_KEM_768.encaps(st.session_state.ek)
                    nonce = os.urandom(12)
                    cif = AESGCM(sk).encrypt(nonce, pass_q.encode(), None)
                    db_guardar_credencial(1, serv, "usuario", ct, cif, nonce)
                    st.success(f"✅ Guardado para {serv}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    st.session_state.generating = False
        else:
            st.error("Escribe el nombre del servicio.")

elif opcion == "📋 Mi Cofre":
    st.title("📋 Tus Secretos")
    conn = sqlite3.connect("vault.db")
    items = conn.execute("SELECT id, servicio FROM credenciales").fetchall()
    conn.close()

    if not items:
        st.info("Cofre vacío.")
    else:
        for rid, serv in items:
            with st.expander(f"🔐 {serv}"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("👁️ Revelar", key=f"rev_{rid}"):
                        ct, cif, non = db_obtener_secreto_completo(rid)
                        # Desencapsulación Kyber
                        sk_rec = ML_KEM_768.decaps(st.session_state.dk, ct)
                        pf = AESGCM(sk_rec).decrypt(non, cif, None).decode()
                        st.code(pf)
                with c2:
                    if st.checkbox("Confirmar borrado", key=f"chk_{rid}"):
                        if st.button("🗑️ Borrar", key=f"del_{rid}", type="primary"):
                            db_borrar_credencial(rid)
                            st.rerun()