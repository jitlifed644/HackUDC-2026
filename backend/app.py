import streamlit as st
import os
import sqlite3
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv
from collections import Counter
import math
from security import derivar_llave_maestra 
from database import (
    inicializar_db, guardar_config_inicial, 
    db_guardar_credencial, db_obtener_secreto_completo
) 
from kyber_py.ml_kem import ML_KEM_768 
from quantum_random import generacion_contraseñas, calcular_entropia #

# 1. CONFIGURACIÓN INICIAL (DEBE SER LO PRIMERO)
st.set_page_config(page_title="PQC Quantum Vault", page_icon="🔐", layout="wide")

load_dotenv()
api_key = os.getenv("IBM_QUANTUM_TOKEN")

# Inicialización física de la base de datos
inicializar_db()

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# ======================== LÓGICA DE SEGURIDAD ========================

def es_password_segura(password):
    """Valida los requisitos físicos de la Master Password."""
    if len(password) < 12:
        return False, "⚠️ Mínimo 12 caracteres."
    if not any(c.isupper() for c in password):
        return False, "⚠️ Falta una MAYÚSCULA."
    if not any(c.islower() for c in password):
        return False, "⚠️ Falta una minúscula."
    if not any(c.isdigit() for c in password):
        return False, "⚠️ Falta un número."
    
    caracteres_especiales = "!@#$%^&*" 
    if not any(c in caracteres_especiales for c in password):
        return False, f"⚠️ Falta un carácter especial ({caracteres_especiales})."
    
    return True, ""

# ======================== PANTALLA DE ACCESO ========================

def pantalla_login():
    st.title("🔐 Acceso a la Bóveda Post-Cuántica")
    
    conn = sqlite3.connect("vault.db")
    # SELECT explícito para garantizar integridad de los datos
    config = conn.execute("SELECT ek, dk_cifrada, salt, nonce_dk FROM configuracion WHERE id=1").fetchone()
    conn.close()

    if not config:
        st.warning("✨ Configuración de nueva Bóveda (Primera vez)")
        st.markdown("Requisitos: 12+ caracteres, [A-Z], [a-z], [0-9] y [!@#$%^&*]")
        
        # Mantenemos vuestra lógica de registro con entropía
        m_pass = st.text_input("Define tu Master Password", type="password")
        
        confirmar_riesgo = False
        h_val = 0

        if m_pass:
            h_val = calcular_entropia(m_pass) 
            progreso = min(h_val / 4.5, 1.0)
            
            if h_val < 2.5:
                st.error(f"🔴 Muy Débil ($H = {h_val:.2f}$)")
            elif h_val < 3.5:
                st.warning(f"🟡 Moderada ($H = {h_val:.2f}$)")
            else:
                st.success(f"🟢 Fuerte ($H = {h_val:.2f}$)")
            
            st.progress(progreso)

            if h_val < 3.2:
                st.info("Patrones repetitivos detectados.")
                confirmar_riesgo = st.checkbox("Acepto el riesgo de baja entropía.")

        if st.button("🚀 Crear y Sellar Bóveda"):
            valida, mensaje = es_password_segura(m_pass)
            if not valida:
                st.error(mensaje)
            elif h_val < 3.2 and not confirmar_riesgo:
                st.error("❌ Confirma el riesgo de entropía baja.")
            else:
                with st.spinner("Generando identidad PQC..."):
                    try:
                        # Identidad Kyber y blindaje Argon2id
                        ek, dk = ML_KEM_768.keygen()
                        salt = os.urandom(16)
                        master_key = derivar_llave_maestra(m_pass, salt)
                        nonce_dk = os.urandom(12)
                        dk_cifrada = AESGCM(master_key).encrypt(nonce_dk, dk, None)
                        
                        guardar_config_inicial(ek, dk_cifrada, salt, nonce_dk)
                        
                        # Inyectamos en RAM y saltamos el login 
                        st.session_state.dk = dk 
                        st.session_state.ek = ek
                        st.session_state.unlocked = True
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en creación: {e}")
    else:
        
        with st.form("login_form", clear_on_submit=False):
            # Añadimos key="pwd_login" para forzar el guardado en session_state
            st.text_input("Introduce tu Master Password", type="password", key="pwd_login")
            submit = st.form_submit_button("Desbloquear")
            
            if submit:
                # Leemos directamente del estado de la clave (key) 
                m_pass_input = st.session_state.pwd_login
                db_ek, db_dk_c, db_salt, db_nonce_dk = config
                
                with st.spinner("Abriendo búnker..."):
                    m_key = derivar_llave_maestra(m_pass_input, db_salt) #
                    try:
                        # Desencriptado de la DK de Kyber 
                        st.session_state.dk = AESGCM(m_key).decrypt(db_nonce_dk, db_dk_c, None)
                        st.session_state.ek = db_ek
                        st.session_state.unlocked = True
                        
                        # Higiene: Borramos la pass en texto claro de la sesión 
                        del st.session_state.pwd_login
                        
                        st.rerun()
                    except Exception:
                        st.error("Acceso denegado. Contraseña incorrecta.")

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
    st.success("Identidad verificada en RAM. Bóveda desbloqueada.")

elif opcion == "➕ Generar":
    st.title("➕ Generar Nueva Credencial")
    
    # 1. Inicializamos el estado de generación si no existe
    if "generating" not in st.session_state:
        st.session_state.generating = False

    serv = st.text_input("Nombre del Servicio", disabled=st.session_state.generating)
    long = st.slider("Longitud", 12, 32, 20, disabled=st.session_state.generating)
    
    # 2. El botón se deshabilita si ya hay una generación en curso
    if st.button("Generar con IBM Quantum", disabled=st.session_state.generating):
        if not serv:
            st.error("Ponle un nombre al servicio.")
        else:
            st.session_state.generating = True
            st.rerun() # Forzamos recarga para que el botón aparezca deshabilitado

    # 3. Lógica de ejecución bloqueante
    if st.session_state.generating:
        with st.spinner("⏳ Obteniendo entropía cuántica de IBM... Por favor, espera."):
            try:
                # Generación real
                pass_q = generacion_contraseñas(long)
                
                # Cifrado PQC
                shared_key, ct = ML_KEM_768.encaps(st.session_state.ek)
                nonce = os.urandom(12)
                cifrado = AESGCM(shared_key).encrypt(nonce, pass_q.encode(), None)
                
                # Guardado
                db_guardar_credencial(1, serv, "usuario", ct, cifrado, nonce)
                st.success(f"¡{serv} guardado con éxito!")
                st.balloons()
            except Exception as e:
                st.error(f"Fallo en la generación: {e}")
            finally:
                # 4. LIBERAR EL BOTÓN siempre, pase lo que pase
                st.session_state.generating = False
                st.rerun()

elif opcion == "📋 Mi Cofre":
    st.title("📋 Tus Secretos")
    conn = sqlite3.connect("vault.db")
    items = conn.execute("SELECT id, servicio FROM credenciales").fetchall()
    conn.close()

    if not items:
        st.info("El cofre está vacío.")
    else:
        for rid, serv in items:
            with st.expander(f"🔐 {serv}"):
                # FIX: Se eliminó cualquier llamada a calcular_entropia aquí 
                if st.button("Revelar", key=f"btn_{rid}"):
                    ct, cif, non = db_obtener_secreto_completo(rid) #
                    sk_rec = ML_KEM_768.decaps(st.session_state.dk, ct) # 
                    pass_f = AESGCM(sk_rec).decrypt(non, cif, None).decode()
                    st.code(pass_f)