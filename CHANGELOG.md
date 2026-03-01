# Changelog - Zero-State Defense

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [1.0.0] - 2026-03-01 (HackUDC Release)

### Añadido
* **Motor PQC**: Implementación de ML-KEM-768 (Kyber) para encapsulación de claves de sesión [cite: ml_kem.py, app.py].
* **Blindaje KDF**: Derivación de llave maestra mediante Argon2id con coste de memoria de 64MB [cite: security.py, app.py].
* **IBM Quantum Integration**: Fuente de entropía real desde hardware cuántico para generación de contraseñas [cite: quantum_random.py].
* **Bóveda Reactiva**: Interfaz de usuario en Streamlit con gestión de estado Zero-Knowledge [cite: app.py].
* **Testing Suite**: Script de integración completa para validar el flujo criptográfico [cite: prueba.py].

### Corregido
* **UX Bug**: Solución al problema de doble clic en el formulario de login mediante sincronización de RAM [cite: app.py, 2026-03-01].
* **Entropía Check**: Ajuste en la validación del 70% de entropía Shannon para mayor robustez [cite: imagen.png, quantum_random.py].
* **Estabilidad Qiskit**: Corrección de errores en la ejecución de circuitos ISA para hardware IBM [cite: imagen.png, quantum_random.py].

### Cambiado
* **Simplificación de Seguridad**: Transición a un modelo de "Soberanía Total" sin mecanismos de recuperación externos para maximizar la privacidad [cite: 2026-03-01, app.py].
* **Esquema de Base de Datos**: Actualización de SQLite para soportar identidad cuántica [cite: database.py].

### Eliminado
* **Google Authenticator**: Removido por razones de arquitectura de recuperación circular [cite: 2026-03-01, app.py].
* **Recovery Key**: Eliminación de la llave de 32 bytes para simplificar la experiencia de usuario [cite: 2026-03-01, app.py].

---
*Este changelog documenta el desarrollo intensivo de Zero-State Defense durante las 36h de HackUDC.*