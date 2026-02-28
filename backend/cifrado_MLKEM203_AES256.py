# contrasena_ml_kem_aes.py
# Demo: genera claves ML-KEM-768 → encapsula → cifra contraseña con AES-256-GCM → simula recuperación

from kyber_py.ml_kem import ML_KEM_768
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# ========================
# TU FUNCIÓN REAL DE CONTRASEÑA CUÁNTICA (cámbiala por la tuya)
# ========================
from quantum_random import generacion_contraseñas

# ========================
# 1. Generar par de claves ML-KEM-768 (solo una vez por usuario/sesión)
# ========================
ek, dk = ML_KEM_768.keygen()
print("Claves ML-KEM generadas:")
print(f"  Publica (ek): {len(ek)} bytes")
print(f"  Privada (dk): {len(dk)} bytes")

# ========================
# 2. Encapsulación: generar clave simétrica k + ciphertext ML-KEM
# ========================
shared_key, ciphertext_ml_kem = ML_KEM_768.encaps(ek)
print("\nEncapsulación OK:")
print(f"  Clave simétrica k: {len(shared_key)} bytes (32)")
print(f"  Ciphertext ML-KEM: {len(ciphertext_ml_kem)} bytes (~1088)")

# ========================
# 3. Generar y cifrar la contraseña con AES-256-GCM usando k
# ========================
contrasena = generacion_contraseñas(20)
contrasena_bytes = contrasena.encode('utf-8')

# Nonce aleatorio seguro (12 bytes recomendado para GCM)
nonce = os.urandom(12)

# Cifrar con AES-256-GCM
aesgcm = AESGCM(shared_key)
cifrado = aesgcm.encrypt(nonce, contrasena_bytes, None)  # None = sin associated data

print("\nCifrado completado:")
print(f"  Contraseña original: {contrasena}")
print(f"  Nonce (hex): {nonce.hex()}")
print(f"  Cifrado (hex): {cifrado.hex()}")
print(f"  Longitud cifrado: {len(cifrado)} bytes")

# ========================
# 4. Simulación de recuperación (lo que haría el PC después)
# ========================
# Decapsular para recuperar la misma k
shared_key_recuperada = ML_KEM_768.decaps(dk, ciphertext_ml_kem)

# Verificar que es la misma (en producción no imprimas)
assert shared_key == shared_key_recuperada, "¡Error! Claves no coinciden"

# Descifrar
aesgcm_rec = AESGCM(shared_key_recuperada)
contrasena_recuperada_bytes = aesgcm_rec.decrypt(nonce, cifrado, None)
contrasena_recuperada = contrasena_recuperada_bytes.decode('utf-8')

print("\nRecuperación OK:")
print(f"  Contraseña recuperada: {contrasena_recuperada}")
print("  Coincide con original:", contrasena_recuperada == contrasena)

# ========================
# Qué guardarías en DB / dar al usuario
# ========================
# - ciphertext_ml_kem (1088 bytes) → al usuario o DB
# - nonce (12 bytes) + cifrado (longitud variable) → en DB cifrada/at-rest
# - dk → SOLO en el PC (HSM o memoria segura, nunca en DB plana)