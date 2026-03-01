# Zero-State Defense: Post-Quantum Vault

Zero-State Defense es una boveda de contraseñas de 'Cero Conocimiento' (Zero-Knowledge) diseñada para aplicar a dia de hoy y en la era post-cuantica. Integramos criptografia de vanguardia y hardware cuantico real para ofrecer una soberania digital absoluta.

---

## Caracteristicas Principales

* **Criptografia Post-Cuantica (PQC)**: Implementacion de ML-KEM-768 (Kyber) para blindar tus secretos contra futuros ataques cuanticos.
* **Entropia Cuantica Real**: Las contraseñas se generan mediante circuitos cuanticos ejecutados en hardware real de IBM Quantum.
* **Blindaje Argon2id**: La derivacion de tu Master Password utiliza el estandar ganador del Password Hashing Competition para resistencia maxima.
* **Arquitectura de Conocimiento Cero**: Tu identidad cuantica solo reside en la memoria RAM volatil mientras la boveda esta abierta.

---

## Flujo Tecnico

```text
[ Usuario ] -> (Master Password) -> [ Argon2id KDF ]
                                           |
                                           v
[ IBM Quantum ] -> (Entropia Shannon) -> [ Generador de Credenciales ]
                                           |
                                           v
[ Boveda SQLite ] <- (Kyber ML-KEM-768) <- [ Cifrado AESGCM-256 ]
```

---

## Instalacion y Uso

1. **Requisitos**: Python 3.10+ e instalar dependencias desde un entorno virtual `python3 -m venv .venv` con `pip install -r requirements.txt`.
2. **Hardware**: Crea un archivo `.env` en la raiz con tu `IBM_QUANTUM_TOKEN`.
3. **Ejecucion**: Lanza la boveda con `streamlit run backend/app.py`.

---

## Diario de la Hackathon (HackUDC 2026)

Este proyecto nacio en 36 horas de desarrollo intensivo. Durante el proceso hemos:
1. **Iterado el Login**: Corregido bugs de sincronizacion de RAM en Streamlit para asegurar un acceso instantaneo.
2. **Validado la Fisica**: Implementado checks de entropia de Shannon locales para asegurar que el hardware cuantico entregue bits aleatorios puros.
3. **Simplificado para la Libertad**: Eliminado mecanismos de recuperacion para garantizar que solo tu seas el dueno de tus datos.

---

## Licencia y Equipo

* **Licencia**: Apache 2.0.
* **Equipo**: Hugo Lario Citoula & Alvaro Sampedro Rodriguez.

> 'En la era cuantica, la privacidad no es un lujo, es una constante fisica.'