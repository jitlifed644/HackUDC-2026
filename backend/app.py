import streamlit as st
import os
import sqlite3
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("IBM_QUANTUM_TOKEN")

# Configuración de página: DEBE SER EL PRIMER COMANDO DE STREAMLIT
st.set_page_config(page_title="PQC Quantum Vault", page_icon="🔐", layout="wide")

# Imports locales
from security import derivar_llave_maestra #
from database import (
    inicializar_db, guardar_config_inicial, 
    db_guardar_credencial, db_obtener_secreto_completo
) #
from kyber_py.ml_kem import ML_KEM_768 #
from quantum_random import generacion_contraseñas #

# Inicialización de la DB física
inicializar_db()

# Manejo de estado de sesión [cite: 2026-01-06]
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# ======================== PANTALLA DE LOGIN ========================
def pantalla_login():
    st.title("🔐 Acceso a la Bóveda Post-Cuántica")
    
    conn = sqlite3.connect("vault.db")
    # Aseguramos el orden correcto de las columnas según database.py
    config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk FROM configuracion WHERE id=1").fetchone()
    conn.close()

    if not config:
        st.warning("✨ Primera vez detectada. Crea tu Master Password.")
        m_pass = st.text_input("Nueva Master Password", type="password")
        if st.button("Configurar Bóveda"):
            if len(m_pass) < 4:
                st.error("Usa una contraseña más larga para mayor seguridad.")
            else:
                # Generación de Identidad [cite: 2025-10-16]
                ek, dk = ML_KEM_768.keygen()
                salt = os.urandom(16)
                m_key = derivar_llave_maestra(m_pass, salt) #
                n_dk = os.urandom(12)
                dk_c = AESGCM(m_key).encrypt(n_dk, dk, None)
                # Guardamos en el orden exacto de la DB
                guardar_config_inicial(ek, dk_c, salt, n_dk)
                st.success("Bóveda creada. ¡Introduce tu contraseña para entrar!")
                st.rerun()
    else:
        m_pass = st.text_input("Introduce tu Master Password", type="password")
        if st.button("Desbloquear"):
            # Recuperamos en el orden exacto del SELECT [cite: 2026-01-06]
            ek, dk_c, salt, n_dk = config
            m_key = derivar_llave_maestra(m_pass, salt)
            try:
                # Intento de desencriptado en RAM [cite: 2026-01-06]
                st.session_state.dk = AESGCM(m_key).decrypt(n_dk, dk_c, None)
                st.session_state.ek = ek
                st.session_state.unlocked = True
                st.rerun()
            except Exception as e:
                st.error(f"Acceso denegado: Verifica tu contraseña.")

if not st.session_state.unlocked:
    pantalla_login()
    st.stop()

# ======================== INTERFAZ PRINCIPAL ========================
st.sidebar.title("🛡️ PQC Vault v1.0")
opcion = st.sidebar.radio("Navegación", ["🏠 Inicio", "➕ Generar", "📋 Mi Cofre"])

if st.sidebar.button("🔒 Cerrar Bóveda"):
    st.session_state.unlocked = False
    st.rerun()

if opcion == "🏠 Inicio":
    st.title("🚀 Bóveda Activa")
    st.success("Identidad cuántica verificada y cargada en RAM.")

elif opcion == "➕ Generar":
    st.title("➕ Generar Nueva Credencial")
    serv = st.text_input("Nombre del Servicio")
    long = st.slider("Longitud", 12, 32, 20)
    
    if st.button("Generar con IBM Quantum"):
        with st.spinner("Obteniendo entropía cuántica..."):
            pass_q = generacion_contraseñas(long) #
            # Encapsulación con la llave de sesión [cite: 2025-10-16]
            shared_key, ct = ML_KEM_768.encaps(st.session_state.ek)
            nonce = os.urandom(12)
            cifrado = AESGCM(shared_key).encrypt(nonce, pass_q.encode(), None)
            # Guardado persistente
            db_guardar_credencial(1, serv, "usuario", ct, cifrado, nonce)
            st.success(f"¡{serv} guardado bajo cifrado post-cuántico!")

elif opcion == "📋 Mi Cofre":
    st.title("📋 Tus Secretos")
    conn = sqlite3.connect("vault.db")
    items = conn.execute("SELECT id, servicio FROM credenciales").fetchall()
    conn.close()

    for rid, serv in items:
        with st.expander(f"🔐 {serv}"):
            if st.button("Revelar", key=f"btn_{rid}"):
                ct, cif, non = db_obtener_secreto_completo(rid) #
                # Decapsulado con la llave privada de la RAM [cite: 2026-01-06]
                sk_rec = ML_KEM_768.decaps(st.session_state.dk, ct)
                pass_f = AESGCM(sk_rec).decrypt(non, cif, None).decode()
                st.code(pass_f)