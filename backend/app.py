# app.py
import streamlit as st
import os
from datetime import datetime
from kyber_py.ml_kem import ML_KEM_768
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import sqlite3
import traceback

# ======================== IMPORT CUÁNTICO ========================
try:
    from quantum_random import generacion_contraseñas
except ImportError:
    st.error("No se encuentra el módulo quantum_random.py")
    st.stop()

# ======================== CONFIGURACIÓN ========================
st.set_page_config(
    page_title="Quantum ML-KEM Demo",
    page_icon="🔐",
    layout="wide"
)

KEYS_DIR = "./local_private_keys"
os.makedirs(KEYS_DIR, exist_ok=True)

# ======================== BASE DE DATOS ========================
conn = sqlite3.connect("secure_keys.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ciphertext_ml_kem BLOB NOT NULL,
    nonce BLOB NOT NULL,
    cifrado BLOB NOT NULL
)
""")
conn.commit()

# ======================== ESTADO ========================
if "mode" not in st.session_state:
    st.session_state.mode = "menu"
if "step" not in st.session_state:
    st.session_state.step = 1
if "temp_data" not in st.session_state:
    st.session_state.temp_data = {}

# ======================== SIDEBAR ========================
with st.sidebar:
    st.title("Quantum ML-KEM")
    st.caption("Demo HackUDC 2026")

    st.divider()

    if st.button("🏠 Menú principal", use_container_width=True):
        st.session_state.mode = "menu"
        st.session_state.step = 1
        st.session_state.temp_data = {}
        st.rerun()

    if st.button("➕ Nueva contraseña", type="primary", use_container_width=True):
        st.session_state.mode = "crear"
        st.session_state.step = 1
        st.session_state.temp_data = {}
        st.rerun()

    if st.button("📋 Lista de contraseñas", use_container_width=True):
        st.session_state.mode = "listar"
        st.rerun()

# ======================================================
# MENÚ PRINCIPAL
# ======================================================
if st.session_state.mode == "menu":
    st.title("🔐 Generador Post-Cuántico Seguro")
    st.markdown("**Demo HackUDC 2026**")

    st.markdown("""
    • ML-KEM-768 (Kyber)  
    • AES-256-GCM  
    • Entropía cuántica real (IBM Quantum + fallback)
    """)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Generar nueva contraseña", type="primary", use_container_width=True):
            st.session_state.mode = "crear"
            st.session_state.step = 1
            st.rerun()

    with col2:
        if st.button("📋 Ver / recuperar contraseñas", use_container_width=True):
            st.session_state.mode = "listar"
            st.rerun()

    st.info("Claves privadas → carpeta `./local_private_keys` (solo este equipo)")

# ======================================================
# LISTAR + RECUPERAR
# ======================================================
elif st.session_state.mode == "listar":
    st.title("📋 Contraseñas guardadas")
    st.markdown("**Carpeta de claves privadas:** `./local_private_keys`")
    st.caption("Usa el archivo `key_{ID}.bin` correspondiente para recuperar la contraseña")

    c.execute("SELECT id, name, created_at FROM generations ORDER BY id DESC")
    rows = c.fetchall()

    if not rows:
        st.info("Aún no hay contraseñas guardadas.")
    else:
        st.success(f"{len(rows)} contraseñas encontradas")

        for rid, name, fecha in rows:
            key_file = f"key_{rid}.bin"
            key_path = os.path.join(KEYS_DIR, key_file)

            with st.expander(f"🔑 {name} — {fecha} (ID {rid})", expanded=False):
                st.markdown("**Clave privada asociada**")
                if os.path.exists(key_path):
                    st.code(key_path)
                    st.caption("Archivo encontrado ✓")
                else:
                    st.error("Archivo de clave privada NO encontrado")
                    continue  # pasa al siguiente sin intentar descifrar

                st.divider()
                st.subheader("Recuperar contraseña")

                key_input = st.text_input(
                    "Ruta completa al archivo .bin",
                    value=key_path,
                    key=f"path_input_{rid}"
                )

                if st.button("Confirmar y descifrar", type="primary", key=f"btn_desc_{rid}"):
                    placeholder = st.empty()
                    try:
                        placeholder.info("1. Leyendo clave privada del disco...")
                        with open(key_input, "rb") as f:
                            dk = f.read()

                        placeholder.info("2. Consultando datos cifrados de la base de datos...")
                        c.execute("SELECT ciphertext_ml_kem, nonce, cifrado FROM generations WHERE id = ?", (rid,))
                        resultado = c.fetchone()
                        if not resultado:
                            raise ValueError("No se encontró el registro en la base de datos")

                        ct, nonce, cifrado = resultado

                        placeholder.info("3. Decapsulando con ML-KEM-768...")
                        shared_key_rec = ML_KEM_768.decaps(dk, ct)

                        placeholder.info("4. Inicializando AES-256-GCM con la clave recuperada...")
                        aesgcm_rec = AESGCM(shared_key_rec)

                        placeholder.info("5. Descifrando el contenido...")
                        bytes_rec = aesgcm_rec.decrypt(nonce, cifrado, None)

                        placeholder.info("6. Decodificando a texto UTF-8...")
                        password_rec = bytes_rec.decode('utf-8')

                        placeholder.success("¡Recuperación completada!")
                        st.success("Contraseña recuperada:")
                        st.code(password_rec, language="text")

                    except Exception as e:
                        placeholder.error("FALLO EN LA RECUPERACIÓN")
                        with st.expander("¿Qué ha fallado exactamente?", expanded=True):
                            st.markdown(f"**Tipo de error:** `{type(e).__name__}`")
                            st.markdown(f"**Mensaje:** {str(e)}")
                            st.markdown("**Traceback completo (para depuración):**")
                            st.code(traceback.format_exc(), language="python")

    st.divider()
    if st.button("← Volver al menú principal", use_container_width=True):
        st.session_state.mode = "menu"
        st.rerun()

# ======================================================
# CREAR (contraseña NUNCA se muestra)
# ======================================================
elif st.session_state.mode == "crear":
    st.title("➕ Crear nueva contraseña segura")

    if st.button("← Cancelar y volver", type="secondary"):
        st.session_state.mode = "menu"
        st.session_state.step = 1
        st.session_state.temp_data = {}
        st.rerun()

    st.divider()

    if st.session_state.step == 1:
        st.subheader("Paso 1 – Información")
        name = st.text_input("Nombre / etiqueta", placeholder="trabajo_2026 • correo_personal • wallet_cold...")
        length = st.slider("Longitud", 12, 32, 20)

        if st.button("Generar y cifrar contraseña →", type="primary"):
            if not name.strip():
                st.error("Introduce un nombre")
            else:
                with st.spinner("Generando entropía cuántica..."):
                    try:
                        password = generacion_contraseñas(length)
                        st.session_state.temp_data = {
                            "name": name,
                            "password_bytes": password.encode('utf-8'),
                            "length": length
                        }
                        st.session_state.step = 2
                        st.rerun()
                    except Exception as e:
                        st.error("Fallo en generación")
                        st.code(str(e))

    elif st.session_state.step == 2:
        st.subheader("Paso 2 – Cifrado inmediato")
        st.info("La contraseña se ha generado de forma segura y **no se muestra en pantalla**.")
        st.info("Se va a cifrar ahora con ML-KEM-768 + AES-256-GCM")

        if st.button("Cifrar y guardar", type="primary"):
            with st.spinner("Cifrando con ML-KEM-768 + AES-GCM..."):
                try:
                    ek, dk = ML_KEM_768.keygen()
                    shared_key, ciphertext_ml_kem = ML_KEM_768.encaps(ek)
                    nonce = os.urandom(12)
                    aesgcm = AESGCM(shared_key)
                    cifrado = aesgcm.encrypt(
                        nonce,
                        st.session_state.temp_data["password_bytes"],
                        None
                    )

                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("""
                        INSERT INTO generations (name, created_at, ciphertext_ml_kem, nonce, cifrado)
                        VALUES (?, ?, ?, ?, ?)
                    """, (st.session_state.temp_data["name"], fecha, ciphertext_ml_kem, nonce, cifrado))
                    conn.commit()

                    rid = c.lastrowid
                    key_path = os.path.join(KEYS_DIR, f"key_{rid}.bin")
                    with open(key_path, "wb") as f:
                        f.write(dk)

                    st.session_state.temp_data = {
                        "name": st.session_state.temp_data["name"],
                        "rid": rid,
                        "key_path": key_path
                    }
                    if "password_bytes" in st.session_state.temp_data:
                        del st.session_state.temp_data["password_bytes"]

                    st.session_state.step = 3
                    st.rerun()

                except Exception as e:
                    st.error("Error al cifrar/guardar")
                    st.code(str(e))

    elif st.session_state.step == 3:
        st.success("¡Contraseña generada, cifrada y guardada correctamente!")
        st.markdown("**La contraseña nunca se mostró en pantalla.**")
        st.markdown("Solo puedes verla desde la lista usando la clave privada.")

        st.divider()
        st.markdown(f"**Nombre:** {st.session_state.temp_data['name']}")
        st.markdown(f"**ID:** {st.session_state.temp_data['rid']}")
        st.markdown("**Clave privada guardada en:**")
        st.code(st.session_state.temp_data["key_path"])

        st.warning("Sin esta clave privada NO podrás recuperar la contraseña.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ver lista de contraseñas", type="primary"):
                st.session_state.mode = "listar"
                st.session_state.step = 1
                st.session_state.temp_data = {}
                st.rerun()
        with col2:
            if st.button("Volver al menú"):
                st.session_state.mode = "menu"
                st.session_state.step = 1
                st.session_state.temp_data = {}
                st.rerun()

conn.close()