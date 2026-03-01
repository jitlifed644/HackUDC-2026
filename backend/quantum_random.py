import string
import time # Para medir cuánto tarda el hardware real
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit_ibm_runtime import QiskitRuntimeService, RuntimeJobTimeoutError
import math
from collections import Counter
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager
import os
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

# Obtenemos el token de forma segura
API_KEY = os.getenv("IBM_QUANTUM_TOKEN")

if not API_KEY:
    # Si no hay token, el sistema usará el simulador local (Aer) automáticamente
    print("⚠️ IBM_QUANTUM_TOKEN no encontrado. Usando fallback local.")
def calcular_entropia(texto):
    if not texto: return 0
    frecuencias = Counter(texto)
    longitud = len(texto)
    entropia = -sum((count / longitud) * math.log2(count / longitud) 
                    for count in frecuencias.values())
    return entropia

def seleccionar_backend_inteligente(service, max_cola=3):
    backends = service.backends(simulator=False, operational=True)
    if not backends:
        raise Exception("No hay backends reales operativos.")
    
    mejor = min(backends, key=lambda b: b.status().pending_jobs)
    cola_actual = mejor.status().pending_jobs
    
    if cola_actual > max_cola:
        raise Exception(f"Cola saturada ({cola_actual} > {max_cola})")
    return mejor

def generacion_contraseñas(caracteres=20, tiempo_max_espera=30, reintentos=0):
    alfabeto = string.ascii_letters + string.digits + "!@#$%^&*"
    n = len(alfabeto)
    umbral_70 = int(caracteres * 0.7)
    
    if not (12 <= caracteres <= 32):
        return -1

    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure(0, 0)
    bits = []

    # --- PARTE A: HARDWARE REAL ---
    inicio_quantum = time.time()
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=API_KEY)
        backend = seleccionar_backend_inteligente(service, max_cola=3) 
        
        # 1. PASO OBLIGATORIO: Crear un circuito ISA (Instruction Set Architecture)
        # Esto adapta tu circuito a la disposición física de ibm_fez
        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_circuit = pm.run(qc)
        
        # 2. USAR EL SAMPLER
        sampler = Sampler(mode=backend)

        
        job = sampler.run([isa_circuit], shots=caracteres * 8)
        result = job.result(timeout=tiempo_max_espera)
        
        # 3. EXTRAER BITS (Cambia la forma de obtener los datos)
        # Accedemos al primer 'pub' (Public Result) y a sus bits de medida
        pub_result = result[0]
        registro_nombre = list(pub_result.data.keys())[0]
        bits = pub_result.data[registro_nombre].get_bitstrings()
        print("IBM Quantum")

    # --- PARTE B: FALLBACK ---
    except Exception as e:

        backend = Aer.get_backend('qasm_simulator') 
        t_qc = transpile(qc, backend)
        job = backend.run(t_qc, shots=caracteres * 8, memory=True)
        bits = job.result().get_memory()
        print("Emulador cuantico")

    # --- PARTE C: TRADUCCIÓN Y ENTROPÍA ---
    args = [iter(bits)] * 8
    password = ""

    for i, p in enumerate(zip(*args)):
        byte_str = "".join(p)
        valor_decimal = int(byte_str, 2)
        password += alfabeto[valor_decimal % n]

        # Fase 1: Check temprano (8 caracteres)
        if i == 7:
            h_inicial = calcular_entropia(password)
            print(f"📊 [CHECK 1] Caracteres: 8 | Entropía Shannon: {h_inicial:.4f}")
            if h_inicial < 2.0:
                return generacion_contraseñas(caracteres, reintentos=reintentos+1)

        # Fase 2: Tu idea del 70%
        if i == umbral_70:
            h_70 = calcular_entropia(password)
            print(f"📊 [CHECK 2] Caracteres: {i+1} (70%) | Entropía Shannon: {h_70:.4f}")
            if h_70 < 2.8:
                return generacion_contraseñas(caracteres, reintentos=reintentos+1)
    
    return password
