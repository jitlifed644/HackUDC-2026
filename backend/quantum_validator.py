import math
from collections import Counter

def validar_contrasena(contrasena: str, 
                      longitud_min: int = 14,
                      entropia_min: float = 95.0) -> tuple[bool, str]:
    """
    Valida la contraseña generada.
    Retorna: (es_valida: bool, mensaje: str)
    """
    if not contrasena:
        return False, "Contraseña vacía"

    longitud = len(contrasena)
    if longitud < longitud_min:
        return False, f"Longitud insuficiente ({longitud} < {longitud_min})"

    # 1. Entropía de Shannon (la más importante en tu caso)
    frecuencias = Counter(contrasena)
    probs = [count / longitud for count in frecuencias.values()]
    entropia_por_caracter = -sum(p * math.log2(p) for p in probs if p > 0)
    entropia_total = entropia_por_caracter * longitud

    if entropia_total < entropia_min:
        return False, f"Entropía demasiado baja: {entropia_total:.1f} bits"

    # 2. Diversidad mínima (evita que sea solo números o solo letras)
    categorias = {
        "mayus": any(c.isupper() for c in contrasena),
        "minus": any(c.islower() for c in contrasena),
        "digito": any(c.isdigit() for c in contrasena),
        "simbolo": any(not c.isalnum() for c in contrasena)
    }
    num_categorias = sum(categorias.values())
    if num_categorias < 3:  # al menos 3 de los 4 tipos
        return False, f"Poca diversidad (solo {num_categorias}/4 tipos de caracteres)"

    # Opcional: check muy básico de repetición obvia (puedes quitarlo)
    if len(frecuencias) < longitud // 3:  # menos de ~1/3 caracteres únicos → sospechoso
        return False, "Demasiados caracteres repetidos"

    return True, f"OK — {longitud} caracteres, {entropia_total:.1f} bits de entropía"