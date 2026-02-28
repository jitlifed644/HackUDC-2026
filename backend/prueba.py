import os
import binascii
from security import derivar_llave_maestra
from database import inicializar_db, guardar_config_inicial, db_guardar_credencial, db_obtener_secreto_completo
from kyber_py.ml_kem import ML_KEM_768
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def test_sistema_completo():
    print("🚀 Iniciando Test de Integración...")
    
    # 1. SETUP: Inicializar DB y Usuario
    inicializar_db() #
    password_hugo = "Uxi2026_SpaceLab"
    salt = os.urandom(16)
    
    print("1. Generando Identidad PQC...")
    ek, dk = ML_KEM_768.keygen()
    
    print("2. Derivando Master Key con Argon2id...")
    master_key = derivar_llave_maestra(password_hugo, salt) #
    
    # Ciframos la DK para el disco
    nonce_dk = os.urandom(12)
    aes_dk = AESGCM(master_key)
    dk_cifrada = aes_dk.encrypt(nonce_dk, dk, None)
    
    guardar_config_inicial(ek, dk_cifrada, salt, nonce_dk) #
    print("✅ Usuario guardado en vault.db")

    # 2. ACCIÓN: Generar y Guardar una Contraseña
    print("\n3. Simulando generación de contraseña cuántica...")
    pass_quantum = "Q-Bits-Vigo-2026-XyZ" # Simulación para no gastar créditos de IBM
    
    # Encapsulación Kyber
    shared_key, ct_pqc = ML_KEM_768.encaps(ek)
    
    # Cifrado AES de la pass
    nonce_p = os.urandom(12)
    aes_p = AESGCM(shared_key)
    pass_enc = aes_p.encrypt(nonce_p, pass_quantum.encode(), None)
    
    db_guardar_credencial(1, "Amazon", "hugo@uvigo.es", ct_pqc, pass_enc, nonce_p) #
    print("✅ Contraseña 'Amazon' sellada y guardada.")

    # 3. VERIFICACIÓN: Recuperar y Abrir
    print("\n4. Intentando recuperar la contraseña...")
    # Simulamos el login: recalculamos master_key con la pass
    master_key_login = derivar_llave_maestra(password_hugo, salt)
    
    # Desencriptamos la DK
    dk_recuperada = aes_dk.decrypt(nonce_dk, dk_cifrada, None)
    
    # Abrimos el sobre de Amazon
    datos = db_obtener_secreto_completo(1) #
    sk_rec = ML_KEM_768.decaps(dk_recuperada, datos[0])
    
    aes_final = AESGCM(sk_rec)
    pass_final = aes_final.decrypt(datos[2], datos[1], None).decode()
    
    if pass_final == pass_quantum:
        print(f"🎉 ¡ÉXITO! Contraseña recuperada: {pass_final}")
    else:
        print("❌ ERROR: La contraseña no coincide.")

if __name__ == "__main__":
    test_sistema_completo()