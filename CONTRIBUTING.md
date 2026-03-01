# 🤝 Guía de Contribución - Zero-State Defense

¡Gracias por interesarte en colaborar con este proyecto de seguridad post-cuántica! Este búnker es Open Source bajo la licencia **Apache 2.0**. Ayúdanos a mantenerlo robusto y a prueba de ataques cuánticos.

---

## 🛠️ Configuración del Entorno de Desarrollo

Sigue estos pasos para poner en marcha el entorno local:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/pqc-vault.git
   cd pqc-vault
   ```

2. **Crear un entorno virtual (Recomendado Python 3.10+):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Hardware Cuántico:**
   Crea un archivo `.env` en la carpeta con tu token de IBM Quantum:
   ```env
   IBM_QUANTUM_TOKEN=tu_token_aqui
   ```

---

## 📜 Estándares de Código y Seguridad

Para garantizar la integridad del sistema, todas las contribuciones deben seguir estas reglas:

* **PEP 8:** El código debe ser limpio, legible y seguir el estilo estándar de Python.
* **Criptografía PQC:** Cualquier cambio en la lógica de cifrado debe basarse en la implementación de **ML-KEM-768 (Kyber)** ya incluida.
* **Zero-Knowledge:** No se aceptarán funciones que almacenen o procesen la Master Password fuera de la memoria RAM volátil.
* **Aleatoriedad:** Usa exclusivamente `os.urandom` o el motor de entropía de `quantum_random.py` para generar sales (salts) y nonces.

---

## 🚩 Convenciones de Commits

Para mantener un historial legible, usamos **Conventional Commits**:

* `feat:` Nueva funcionalidad (ej. `feat: añadir borrado de credenciales`).
* `fix:` Corrección de errores (ej. `fix: bug de sincronización en login`).
* `docs:` Cambios en la documentación o licencias.
* `refactor:` Mejora del código sin cambiar su comportamiento.

---

## 🚀 Proceso de Pull Request (PR)

1. Crea una rama descriptiva: `git checkout -b feat/mejorar-entropia`.
2. Realiza tus cambios y verifica que `app.py` arranca correctamente.
3. Haz un commit siguiendo las convenciones mencionadas.
4. Abre la PR detallando qué mejora de seguridad o rendimiento aporta tu código.

## 🧐 Expectativas de Revisión

Cualquier cambio que afecte a `security.py` o `ml_kem.py` será revisado con especial atención a la **integridad matemática** de la solución y a la entropía de Shannon del sistema.