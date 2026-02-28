# quantum_random.py
# Genera 8 bits verdaderamente aleatorios desde hardware cuántico real de IBM (transpilado)
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("=== Generador de 8 bits cuánticos aleatorios (transpilado) ===\n")

service = QiskitRuntimeService()

print("Buscando backend disponible...")
backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
print(f"→ Usando: {backend.name} ({backend.num_qubits} qubits)")

num_bits = 8
qc = QuantumCircuit(num_bits)
qc.h(range(num_bits))
qc.measure_all()

print("Transpilando circuito para el backend...")
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)
print("→ Circuito transpilado y listo para hardware real\n")

sampler = Sampler(mode=backend)
job = sampler.run([isa_circuit], shots=1)

print(f"Job enviado a '{backend.name}'...")
print("Esperando resultado... (10s a 5-10 min en free tier)\n")

result = job.result()
pub_result = result[0]
counts = pub_result.data.meas.get_counts()
binary_string = max(counts, key=counts.get)

print("Resultado cuántico (verdaderamente aleatorio):")
print(f"  Binario:     {binary_string}")
print(f"  Hexadecimal: 0x{int(binary_string, 2):02X}")
print(f"  Decimal:     {int(binary_string, 2)}")

byte_value = int(binary_string, 2)
if 33 <= byte_value <= 126:
    print(f"  Carácter ASCII imprimible seguro: '{chr(byte_value)}'")
else:
    print(f"  Carácter no imprimible o no seguro (código {byte_value}) → usa hex o decimal directamente")

print("\n¡Éxito! Estos 8 bits vienen de entropía cuántica real.")
print("Úsalos para seeds, bytes de clave, pruebas de cifrado, etc.")