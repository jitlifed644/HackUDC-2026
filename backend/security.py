from argon2 import PasswordHasher
from argon2.low_level import hash_secret_raw, Type

# Para derivar la Master Key de 256 bits
def derivar_llave_maestra(password, salt):
    return hash_secret_raw(
        secret=password.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID
    )