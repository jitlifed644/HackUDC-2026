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

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Zero-State Protection (Quantum Vault)", page_icon="🔐", layout="wide")

load_dotenv()
from security import derivar_llave_maestra #
from database import (
    inicializar_db, guardar_config_inicial, 
    db_guardar_credencial, db_obtener_secreto_completo, db_borrar_credencial
) #
from kyber_py.ml_kem import ML_KEM_768 #
from quantum_random import generacion_contraseñas, calcular_entropia #

inicializar_db()

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "generating" not in st.session_state:
    st.session_state.generating = False

# ======================== LÓGICA DE SEGURIDAD ========================

def es_password_segura(password):
    """Valida los requisitos de la Master Password."""
    if len(password) < 12: return False, "⚠️ Mínimo 12 caracteres."
    if not any(c.isupper() for c in password): return False, "⚠️ Falta una MAYÚSCULA."
    if not any(c.islower() for c in password): return False, "⚠️ Falta una minúscula."
    if not any(c.isdigit() for c in password): return False, "⚠️ Falta un número."
    if not any(c in "!@#$%^&*" for c in password): return False, "⚠️ Falta un símbolo (!@#$%^&*)."
    return True, ""

# ======================== PANTALLA DE ACCESO ========================

def pantalla_login():
    st.title("🔐 Acceso a la Bóveda Post-Cuántica")
    
    conn = sqlite3.connect("vault.db")
    config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk, totp_secret FROM configuracion WHERE id=1").fetchone()
    conn.close()

    # --- FLUJO 1: MOSTRAR KIT TRAS CREACIÓN ---
    if st.session_state.get("setup_complete"):
        st.success("🎉 ¡Bóveda Sellada! Guarda tu Kit de Rescate ahora.")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔑 Recovery Key")
            st.code(st.session_state.recovery_key)
            st.download_button("💾 Descargar Binario", data=st.session_state.recovery_bin, file_name="recovery_identity.bin")
        with c2:
            st.subheader("📱 Google Authenticator")
            qr_img = qrcode.make(st.session_state.totp_uri)
            buf = BytesIO()
            qr_img.save(buf)
            st.image(buf.getvalue(), caption="Escanea este QR")
        
        if st.button("🚀 Entrar a la Bóveda"):
            del st.session_state.setup_complete
            st.session_state.unlocked = True
            st.rerun() # Entra directo tras la creación 
        return

    # --- FLUJO 2: REGISTRO INICIAL ---
    if not config:
        st.warning("✨ Configuración inicial")
        m_pass = st.text_input("Define tu Master Password", type="password")
        if m_pass:
            h = calcular_entropia(m_pass)
            st.progress(min(h/4.5, 1.0), text=f"Entropía: {h:.2f}")

        if st.button("🚀 Crear Bóveda"):
            valida, msg = es_password_segura(m_pass)
            if valida:
                with st.spinner("Generando Identidad PQC..."):
                    try:
                        ek, dk = ML_KEM_768.keygen()
                        salt = os.urandom(16)
                        m_key = derivar_llave_maestra(m_pass, salt)
                        n_dk = os.urandom(12)
                        dk_c = AESGCM(m_key).encrypt(n_dk, dk, None)
                        
                        r_key = generacion_contraseñas(32)
                        totp_sec = pyotp.random_base32()
                        r_salt = os.urandom(16)
                        r_m_key = derivar_llave_maestra(r_key, r_salt)
                        r_n = os.urandom(12)
                        r_blob = AESGCM(r_m_key).encrypt(r_n, dk, None)
                        
                        guardar_config_inicial(ek, dk_c, salt, n_dk, totp_sec) #
                        
                        st.session_state.recovery_key = r_key
                        st.session_state.recovery_bin = r_salt + r_n + r_blob
                        st.session_state.totp_uri = pyotp.totp.TOTP(totp_sec).provisioning_uri(issuer_name="ZS-Protection")
                        st.session_state.setup_complete = True
                        st.session_state.dk, st.session_state.ek = dk, ek
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en la creación: {e}")
            else:
                st.error(msg) # Muestra por qué la contraseña no es válida [cite: 2026-01-06]

    # --- FLUJO 3: LOGIN O RESCATE ---
    else:
        with st.form("login_form", clear_on_submit=False):
            pwd_input = st.text_input("Master Password", type="password")
            submit = st.form_submit_button("Desbloquear")
            
            if submit:
                if not pwd_input:
                    st.warning("⚠️ Por favor, introduce tu contraseña.")
                else:
                    # RE-CONSULTA DENTRO DEL FORM: Asegura datos frescos [cite: 2026-03-01]
                    conn = sqlite3.connect("vault.db")
                    current_config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk, totp_secret FROM configuracion WHERE id=1").fetchone()
                    conn.close()

                    if current_config:
                        ek_db, dk_c_db, salt_db, n_db, _ = current_config
                        
                        with st.spinner("🔓 Derivando llave y abriendo búnker..."):
                            # Derivación de Argon2id
                            m_key = derivar_llave_maestra(pwd_input, salt_db)
                            try:
                                # Intentamos descifrar la DK de Kyber
                                decrypted_dk = AESGCM(m_key).decrypt(n_db, dk_c_db, None)
                                
                                # Si llegamos aquí, todo es correcto. Guardamos en RAM [cite: 2026-01-06]
                                st.session_state.dk = decrypted_dk
                                st.session_state.ek = ek_db
                                st.session_state.unlocked = True
                                st.rerun() 
                            except Exception:
                                # Si falla el descifrado, es que la pass es incorrecta [cite: 2026-03-01]
                                st.error("❌ Contraseña incorrecta. El búnker permanece sellado.")
                    else:
                        st.error("🚨 Error crítico: No se encontró la configuración del búnker.")

        with st.expander("🆘 Rescate de Emergencia (He olvidado mi contraseña)"):
            st.write("Sube tu binario, pon tu clave de 32 caracteres y el código 2FA.")
            file = st.file_uploader("Cargar recovery_identity.bin", type=["bin"])
            rk_in = st.text_input("Recovery Key (32 chars)", type="password")
            otp_in = st.text_input("Código Google Authenticator", max_chars=6)
            new_p = st.text_input("Nueva Master Password", type="password")
            
            if st.button("🔓 Restaurar Acceso"):
                if file and rk_in and otp_in and new_p:
                    totp = pyotp.TOTP(config[4])
                    if totp.verify(otp_in):
                        try:
                            data = file.read()
                            rs, rn, rb = data[:16], data[16:28], data[28:]
                            rmk = derivar_llave_maestra(rk_in, rs)
                            dk_orig = AESGCM(rmk).decrypt(rn, rb, None)
                            
                            ns, nn = os.urandom(16), os.urandom(12)
                            nmk = derivar_llave_maestra(new_p, ns)
                            ndkc = AESGCM(nmk).encrypt(nn, dk_orig, None)
                            
                            conn = sqlite3.connect("vault.db")
                            conn.execute("UPDATE configuracion SET dk_cifrada=?, salt=?, nonce_dk=? WHERE id=1", (ndkc, ns, nn))
                            conn.commit(); conn.close()
                            st.success("✅ Acceso restaurado. Ya puedes loguearte.")
                        except: st.error("❌ Error: Recovery Key o archivo binario incorrectos.")
                    else: st.error("❌ Código 2FA incorrecto.")
                else:
                    st.warning("⚠️ Rellena todos los campos para el rescate.")

if not st.session_state.unlocked:
    pantalla_login()
    st.stop()

# ======================== INTERFAZ PRINCIPAL ========================

st.sidebar.title("🛡️ PQC Vault v1.0")
opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "➕ Generar", "📋 Mi Cofre"], disabled=st.session_state.generating)

if st.sidebar.button("🔒 Cerrar Bóveda", disabled=st.session_state.generating):
    st.session_state.unlocked = False
    st.rerun()

if opcion == "🏠 Inicio":
    st.title("🚀 Bóveda Activa")
    st.success("Identidad verificada en RAM. Bóveda desbloqueada en Vigo.")

elif opcion == "➕ Generar":
    st.title("➕ Nueva Credencial")
    serv = st.text_input("Nombre del Servicio", placeholder="ej. GitHub, MIT, Spotify", disabled=st.session_state.generating)
    long = st.slider("Longitud de Contraseña", 12, 32, 20, disabled=st.session_state.generating)
    
    if st.button("Generar con IBM Quantum", disabled=st.session_state.generating):
        if not serv:
            st.error("⚠️ Debes asignar un nombre al servicio para generar la clave.") 
        else:
            st.session_state.generating = True
            st.rerun()

    if st.session_state.generating:
        with st.spinner("⏳ Conectando con hardware cuántico..."):
            try:
                pass_q = generacion_contraseñas(long)
                sk, ct = ML_KEM_768.encaps(st.session_state.ek)
                nonce = os.urandom(12)
                cif = AESGCM(sk).encrypt(nonce, pass_q.encode(), None)
                db_guardar_credencial(1, serv, "usuario", ct, cif, nonce)
                st.success(f"✅ ¡Contraseña para {serv} generada y guardada!")
                st.balloons()
            except Exception as e:
                st.error(f"Fallo en el enlace cuántico: {e}")
            finally:
                st.session_state.generating = False
                st.rerun()

elif opcion == "📋 Mi Cofre":
    st.title("📋 Tus Secretos")
    conn = sqlite3.connect("vault.db")
    items = conn.execute("SELECT id, servicio FROM credenciales").fetchall()
    conn.close()

    if not items:
        st.info("📭 El cofre está vacío. ¡Empieza a generar seguridad cuántica!") 
    else:
        for rid, serv in items:
            with st.expander(f"🔐 {serv}"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("👁️ Revelar", key=f"rev_{rid}"):
                        ct, cif, non = db_obtener_secreto_completo(rid)
                        sk_rec = ML_KEM_768.decaps(st.session_state.dk, ct)
                        pf = AESGCM(sk_rec).decrypt(non, cif, None).decode()
                        st.code(pf)
                with c2:
                    if st.checkbox("Confirmar borrado.", key=f"chk_{rid}"):
                        if st.button("🗑️ Borrar", key=f"del_{rid}", type="primary"):
                            db_borrar_credencial(rid); st.rerun()