# app.py
import streamlit as st
import os
import binascii
from kyber_py.ml_kem import ML_KEM_768
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ======================== IMPORT CUÁNTICO ========================
from quantum_random import generacion_contraseñas

# Configuración inicial
st.set_page_config(page_title="Quantum ML-KEM Demo", page_icon="🔐", layout="centered")

# CSS para slider, loading giratorio y overlay de bloqueo
st.markdown("""
<style>
    .stSlider {
        padding: 2rem 1rem;
        max-width: 600px;
        margin: 0 auto;
    }
    .stSlider > div > div > div > div {
        height: 16px !important;
    }
    .stSlider > div > div > div > div > div {
        height: 40px !important;
        width: 40px !important;
        border-radius: 50% !important;
    }
    .spinner {
        font-size: 6rem;
        animation: spin 1.5s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.4);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: auto;
    }
    .overlay-content {
        background: white;
        padding: 2rem 3rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        text-align: center;
        font-size: 1.4rem;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Estado inicial
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.length = 20
    st.session_state.generated = False
    st.session_state.user_email = ""

# Validación simple de correo Gmail
def is_valid_gmail(email):
    return "@gmail.com" in email.lower() and len(email) > 10

# ────────────────────────────────────────────────
# PASO 1: Usuario + slider + botón
# ────────────────────────────────────────────────
if st.session_state.step == 1:
    st.title("🔐 Generador Post-Cuántico")
    st.markdown("**Demo HackUDC 2026**")
    st.divider()

    # Apartado de usuario (nuevo)
    st.subheader("Identificación del usuario")
    st.caption("Introduce tu correo Gmail para asociar la generación (opcional pero recomendado)")

    email_input = st.text_input(
        "Correo Gmail",
        value=st.session_state.user_email,
        placeholder="ejemplo@gmail.com",
        help="Solo se usa para asociar esta sesión (no se envía ni almacena externamente en esta demo)"
    )

    if email_input:
        if is_valid_gmail(email_input):
            st.session_state.user_email = email_input
            st.success(f"Correo asociado: {email_input}")
        else:
            st.warning("Por favor introduce un correo Gmail válido (termina en @gmail.com)")

    st.divider()

    st.markdown("<h3 style='text-align: center;'>Elige la longitud de la contraseña</h3>", unsafe_allow_html=True)
    
    length = st.slider(
        label="Longitud",
        min_value=12,
        max_value=32,
        value=st.session_state.length,
        step=1,
        label_visibility="collapsed"
    )
    
    st.markdown(f"<p style='text-align: center; font-size: 1.3rem; margin-top: 1rem;'><strong>{length} caracteres</strong></p>", unsafe_allow_html=True)
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    if st.button("Siguiente → Generar", type="primary", use_container_width=True):
        if not st.session_state.user_email:
            st.warning("Recomendamos asociar un correo antes de continuar")
        st.session_state.length = length
        st.session_state.step = 2
        st.rerun()

# ────────────────────────────────────────────────
# PASO 2: Loading con spinner giratorio + overlay + progreso
# ────────────────────────────────────────────────
elif st.session_state.step == 2:
    # Overlay y spinner inmediato
    st.markdown("""
    <div class="overlay">
        <div class="overlay-content">
            <div class="spinner">⚙️</div>
            <div style="margin-top: 1.5rem;">Generando materiales seguros...</div>
            <div style="margin-top: 0.8rem; font-size: 1.1rem; color: #666;">Por favor espera unos segundos</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    progress = st.empty()

    if not st.session_state.generated:
        progress.info("Iniciando generación de claves post-cuánticas...")
        ek, dk = ML_KEM_768.keygen()

        progress.info("Encapsulando clave simétrica...")
        shared_key, ciphertext_ml_kem = ML_KEM_768.encaps(ek)

        progress.info("Generando contraseña con entropía cuántica...")
        contrasena = generacion_contraseñas(st.session_state.length)
        contrasena_bytes = contrasena.encode("utf-8")

        progress.info("Cifrando con AES-256-GCM...")
        nonce = os.urandom(12)
        aesgcm = AESGCM(shared_key)
        cifrado = aesgcm.encrypt(nonce, contrasena_bytes, None)

        st.session_state.results = {
            "contrasena": contrasena,
            "nonce_hex": nonce.hex(),
            "cifrado_hex": cifrado.hex(),
            "ciphertext_ml_kem_hex": binascii.hexlify(ciphertext_ml_kem).decode(),
            "dk_full_hex": binascii.hexlify(dk).decode(),
        }
        st.session_state.generated = True

        progress.success("¡Proceso completado! Redirigiendo...")
        import time
        time.sleep(1.2)

    st.session_state.step = 3
    st.rerun()

# ────────────────────────────────────────────────
# PASO 3: Resultados (sin "Contraseña recuperada")
# ────────────────────────────────────────────────
elif st.session_state.step == 3:
    st.title("🔐 Resultado Generado")
    st.success("Generación completada correctamente")

    if st.session_state.user_email:
        st.info(f"Asociado al usuario: {st.session_state.user_email}")

    res = st.session_state.results

    st.divider()

    st.subheader("Clave Privada ML-KEM (dk)")
    st.warning("ESTA CLAVE ES EXTREMADAMENTE SENSIBLE – NUNCA LA COMPARTAS")

    with st.expander("Mostrar clave privada completa (solo tú debes verla)", expanded=False):
        st.code(res["dk_full_hex"])
        st.error("Guárdala SOLO en tu dispositivo seguro (HSM, enclave, archivo cifrado con contraseña maestra).")

    st.markdown("""
    ### Instrucciones de uso importantes:
    1. **Guarda la clave privada (dk)** en un lugar extremadamente seguro en tu PC.
    2. **Envía o almacena** los siguientes datos (públicos/cifrados):
       - Ciphertext ML-KEM
       - Nonce
       - Cifrado AES-GCM
    3. La contraseña generada está asociada a esta clave privada.
    4. **No reutilices el mismo par de claves** para varias contraseñas en producción.
    """)

    st.divider()

    st.subheader("Datos para enviar o guardar (sin clave privada)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ciphertext ML-KEM**")
        st.code(res["ciphertext_ml_kem_hex"][:96] + "...")
    with col2:
        st.markdown("**Nonce**")
        st.code(res["nonce_hex"])

    st.markdown("**Cifrado AES-GCM**")
    st.code(res["cifrado_hex"])

    datos_txt = f"""Usuario asociado: {st.session_state.user_email or 'No especificado'}
Ciphertext ML-KEM (hex): {res['ciphertext_ml_kem_hex']}
Nonce (hex): {res['nonce_hex']}
Cifrado AES-GCM (hex): {res['cifrado_hex']}
"""
    st.download_button(
        "⬇️ Descargar datos (sin clave privada)",
        datos_txt,
        file_name="datos_seguros_ml_kem.txt",
        mime="text/plain"
    )

    if st.button("← Generar otra contraseña", use_container_width=True):
        st.session_state.step = 1
        st.session_state.generated = False
        st.rerun()