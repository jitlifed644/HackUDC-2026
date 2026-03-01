# Política de Seguridad - Zero-State Defense

## Nuestro Modelo de Seguridad
Zero-State está construido bajo el principio de **Conocimiento Cero (Zero-Knowledge)**. Esto significa:
* Las claves privadas (DK) y las contraseñas nunca se almacenan en disco de forma legible [cite: app.py, database.py].
* La identidad cuántica solo reside en la memoria RAM volátil mientras la bóveda está desbloqueada [cite: app.py].
* Utilizamos **Argon2id** para la derivación de llaves, protegiendo el sistema contra ataques de fuerza bruta por GPU/ASIC [cite: security.py].
* El cifrado de sesión utiliza el estándar post-cuántico **ML-KEM-768 (Kyber)** [cite: ml_kem.py, prueba.py].

## Versiones Soportadas
| Versión | Soportada |
| ------- | :-------: |
| 1.0.x (HackUDC) | ✅ |

## Reporte de Vulnerabilidades
Si descubres un fallo de seguridad en nuestro código, por favor no abras un issue público. Ayúdanos a proteger la privacidad de los usuarios siguiendo este proceso:
1. Envía un correo electrónico al equipo de **Zero-State Defense**.
2. Proporciona un detalle técnico del fallo y un ejemplo de cómo reproducirlo.
3. Danos un tiempo razonable para solucionar el problema antes de hacerlo público.

## Prácticas de Criptografía
Este proyecto se adhiere a las recomendaciones del NIST para la era post-cuántica. Todas las fuentes de entropía son validadas físicamente mediante hardware de **IBM Quantum**.