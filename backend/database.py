import sqlite3

def inicializar_db():
    """Crea el archivo vault.db y las tablas necesarias."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    
    # Tabla de identidad (solo una fila)
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY,
        ek BLOB,
        dk_cifrada BLOB,
        salt BLOB,
        nonce_dk BLOB
    )''')

    # El cofre de contraseñas
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

def guardar_config_inicial(ek, dk_cifrada, salt, nonce_dk):
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configuracion (id, ek, dk_cifrada, salt, nonce_dk) VALUES (1, ?, ?, ?, ?)",
                   (ek, dk_cifrada, salt, nonce_dk))
    conn.commit()
    conn.close()

# --- ESTAS SON LAS QUE TE FALTAN ---

def db_guardar_credencial(u_id, servicio, u_serv, ct_pqc, p_cifrada, n_pass):
    """Guarda una nueva contraseña cuántica cifrada."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO credenciales 
                      (servicio, usuario_serv, ciphertext_pqc, pass_cifrada, nonce_pass) 
                      VALUES (?, ?, ?, ?, ?)''', 
                   (servicio, u_serv, ct_pqc, p_cifrada, n_pass))
    conn.commit()
    conn.close()

def db_obtener_secreto_completo(cred_id):
    """Recupera los datos cifrados para que el PQC Engine los abra."""
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ciphertext_pqc, pass_cifrada, nonce_pass FROM credenciales WHERE id = ?", (cred_id,))
    res = cursor.fetchone()
    conn.close()
    return res