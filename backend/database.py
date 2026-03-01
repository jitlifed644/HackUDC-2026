import sqlite3

def inicializar_db():
    """Crea el archivo vault.db y las tablas necesarias con soporte 2FA."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    
    # ACTUALIZADO: Añadida la columna totp_secret [cite: 2026-03-01]
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY,
        ek BLOB,
        dk_cifrada BLOB,
        salt BLOB,
        nonce_dk BLOB,
        totp_secret TEXT
    )''')

    # El cofre de contraseñas (Se mantiene igual) [cite: 2025-10-16]
    cursor.execute('''CREATE TABLE IF NOT EXISTS credenciales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        servicio TEXT,
        usuario_serv TEXT,
        ciphertext_pqc BLOB,
        pass_cifrada BLOB,
        nonce_pass BLOB
    )''')
    
    conn.commit()
    conn.close()

def guardar_config_inicial(ek, dk_cifrada, salt, nonce_dk, totp_secret):
    """Guarda la identidad PQC y el secreto de recuperación [cite: 2026-03-01]."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    # Ahora manejamos 5 parámetros
    cursor.execute("""
        INSERT OR REPLACE INTO configuracion (id, ek, dk_cifrada, salt, nonce_dk, totp_secret) 
        VALUES (1, ?, ?, ?, ?, ?)
    """, (ek, dk_cifrada, salt, nonce_dk, totp_secret))
    conn.commit()
    conn.close()

# --- FUNCIONES DE CREDENCIALES ---

def db_guardar_credencial(u_id, servicio, u_serv, ct_pqc, p_cifrada, n_pass):
    """Guarda una nueva contraseña cuántica cifrada [cite: 2025-10-16]."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO credenciales 
                      (servicio, usuario_serv, ciphertext_pqc, pass_cifrada, nonce_pass) 
                      VALUES (?, ?, ?, ?, ?)''', 
                   (servicio, u_serv, ct_pqc, p_cifrada, n_pass))
    conn.commit()
    conn.close()

def db_borrar_credencial(id_credencial):
    """Elimina una credencial por su ID [cite: 2026-01-08]."""
    conn = sqlite3.connect("vault.db")
    conn.execute("DELETE FROM credenciales WHERE id = ?", (id_credencial,))
    conn.commit()
    conn.close()

def db_obtener_secreto_completo(cred_id):
    """Recupera los datos cifrados para el motor Kyber [cite: 2026-03-01]."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ciphertext_pqc, pass_cifrada, nonce_pass FROM credenciales WHERE id = ?", (cred_id,))
    res = cursor.fetchone()
    conn.close()
    return res