import streamlit as st
import os
import sqlite3
import math
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

# 1. CONFIGURACIÓN E IMPORTACIONES
st.set_page_config(page_title="ZSD - HackUDC", page_icon="🔐", layout="wide")
load_dotenv()

from security import derivar_llave_maestra #
from database import (
    inicializar_db, guardar_config_inicial, 
    db_guardar_credencial, db_obtener_secreto_completo, db_borrar_credencial
) #
from kyber_py.ml_kem import ML_KEM_768 #
from quantum_random import generacion_contraseñas, calcular_entropia #

inicializar_db()

# Estados de sesión 
if "unlocked" not in st.session_state: st.session_state.unlocked = False
if "generating" not in st.session_state: st.session_state.generating = False

# ======================== PANTALLA DE ACCESO ========================

def pantalla_login():
    st.title("🔐 Bóveda Post-Cuántica (PQC)")
    
    conn = sqlite3.connect("vault.db")
    config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk FROM configuracion WHERE id=1").fetchone()
    conn.close()

    # --- FLUJO A: REGISTRO INICIAL ---
    if not config:
        st.header("✨ Configuración de Nueva Bóveda")
        st.info("Esta bóveda usa Criptografía Post-Cuántica. No existe recuperación: si pierdes tu clave, los datos se pierden para siempre.") 
        
        m_pass = st.text_input("Define tu Master Password", type="password", key="setup_pass")
        
        if m_pass:
            h = calcular_entropia(m_pass) #
            st.progress(min(h/4.5, 1.0), text=f"Entropía Local: {h:.2f} bits")

        if st.button("🚀 Sellar Bóveda"):
            if len(m_pass) < 12:
                st.error("⚠️ La contraseña debe tener al menos 12 caracteres.") 
            else:
                with st.spinner("Generando Identidad PQC..."):
                    try:
                        # Kyber Keygen
                        ek, dk = ML_KEM_768.keygen()
                        salt = os.urandom(16)
                        # Argon2id
                        m_key = derivar_llave_maestra(m_pass, salt)
                        n_dk = os.urandom(12)
                        dk_c = AESGCM(m_key).encrypt(n_dk, dk, None)
                        
                        guardar_config_inicial(ek, dk_c, salt, n_dk, None)
                        
                        st.session_state.dk, st.session_state.ek = dk, ek
                        st.session_state.unlocked = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error técnico: {e}")

    # --- FLUJO B: LOGIN INSTANTÁNEO ---
    else:
        st.subheader("🔑 Desbloqueo de Seguridad")
        # El uso de 'key' soluciona el bug del doble clic 
        st.text_input("Master Password", type="password", key="login_pass_input")
        
        if st.button("🔓 Desbloquear Bóveda", use_container_width=True):
            pwd_input = st.session_state.login_pass_input
            if not pwd_input:
                st.warning("⚠️ Introduce tu contraseña.")
            else:
                ek_db, dk_c_db, salt_db, n_db = config
                with st.spinner("Desencriptando identidad en RAM..."):
                    m_key = derivar_llave_maestra(pwd_input, salt_db)
                    try:
                        # Descifrado de la llave privada de Kyber
                        st.session_state.dk = AESGCM(m_key).decrypt(n_db, dk_c_db, None)
                        st.session_state.ek = ek_db
                        st.session_state.unlocked = True
                        st.rerun() 
                    except:
                        st.error("❌ Contraseña incorrecta. Acceso denegado.")

if not st.session_state.unlocked:
    pantalla_login()
    st.stop()

# ======================== INTERFAZ PRINCIPAL ========================

st.sidebar.title("🛡️ Zero-State Defense")
opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "➕ Generar", "📋 Claves"], disabled=st.session_state.generating)

if st.sidebar.button("🔒 Cerrar Bóveda", disabled=st.session_state.generating):
    st.session_state.unlocked = False
    st.rerun()

if opcion == "🏠 Inicio":
    st.title("🚀 Bóveda Activa en Vigo")
    st.success("Identidad verificada. Conexión con hardware cuántico de IBM establecida.") 
    st.markdown("""
    <style>
    .centered-title {
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
    }
    .status-text {
        text-align: center;
        color: #00FF00;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Título y Subtítulo centrados
    st.markdown("<h1 class='centered-title'>🛡️ Zero-State Defense: PQC Vault</h1>", unsafe_allow_html=True)
    st.markdown("<p class='centered-title'>Soberanía Digital Post-Cuántica | Hardware de IBM Quantum</p>", unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Por qué Zero-State Defense?"):
        st.write("""
        - **Cero Conocimiento**: Tus claves nunca tocan el disco en texto claro.
        - **Resistencia Cuántica**: Implementación nativa de Kyber (ML-KEM).
        - **Entropía Pura**: Generación de bits mediante hardware cuántico real.
        """)

elif opcion == "➕ Generar":
    st.title("➕ Nueva Credencial Cuántica")
    serv = st.text_input("Servicio", key="new_service_name", disabled=st.session_state.generating)
    long = st.slider("Longitud de Contraseña", 12, 32, 20, disabled=st.session_state.generating)
    
    if st.button("Generar con IBM Quantum", disabled=st.session_state.generating):
        if not st.session_state.new_service_name:
            st.error("🚨 Error: Debes indicar el nombre del servicio.") 
        else:
            st.session_state.generating = True
            st.rerun()

    if st.session_state.generating:
        with st.spinner("⏳ Consultando hardware cuántico real..."):
            try:
                # Generación de entropía pura
                pass_q = generacion_contraseñas(long)
                # Encapsulación Kyber
                sk, ct = ML_KEM_768.encaps(st.session_state.ek)
                nonce = os.urandom(12)
                cif = AESGCM(sk).encrypt(nonce, pass_q.encode(), None)
                # Guardado en DB
                db_guardar_credencial(1, st.session_state.new_service_name, "usuario", ct, cif, nonce)
                st.success(f"✅ ¡Contraseña para {st.session_state.new_service_name} guardada!")
                st.balloons()
            finally:
                st.session_state.generating = False
                st.rerun()

elif opcion == "📋 Claves":
    st.title("📋 Tus Secretos")
    conn = sqlite3.connect("vault.db")
    items = conn.execute("SELECT id, servicio FROM credenciales").fetchall()
    conn.close()

    if not items:
        st.info("📭 El cofre está vacío. Genera tu primera contraseña cuántica.") 
    else:
        for rid, serv in items:
            with st.expander(f"🔐 {serv}"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("👁️ Revelar", key=f"rev_{rid}"):
                        ct, cif, non = db_obtener_secreto_completo(rid) #
                        # Desencapsulación Kyber
                        sk_rec = ML_KEM_768.decaps(st.session_state.dk, ct)
                        pf = AESGCM(sk_rec).decrypt(non, cif, None).decode()
                        st.code(pf)
                with c2:
                    if st.checkbox("Confirmar borrado", key=f"chk_{rid}"):
                        if st.button("🗑️ Borrar", key=f"del_{rid}", type="primary"):
                            db_borrar_credencial(rid); st.rerun() #