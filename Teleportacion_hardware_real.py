from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# ============================================================
# CONFIGURA TU TOKEN AQUÍ
# ============================================================
TOKEN = "kaWOqgYrr_hYzvGTIYeMasRmrPRHFnj2ZlRwBMGasTLm"

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN)

# ============================================================
# CIRCUITO DE TELEPORTACIÓN
# ============================================================
# q0 = qubit con el estado a "enviar" (lo preparamos con una rotación
#      para que no sea trivial, ej. no sea simplemente |0> o |1>)
# q1, q2 = par entrelazado (Bell) que conecta emisor y receptor
# ============================================================

qr = QuantumRegister(3, "q")
cr = ClassicalRegister(3, "c")
qc = QuantumCircuit(qr, cr)

# 1. Preparamos el estado a teletransportar en q0
#    (una superposición no trivial, para que se note el resultado)
qc.h(0)
qc.p(0.5, 0)   # una fase, para que el estado no sea un Bell "obvio"

qc.barrier()

# 2. Creamos el par entrelazado entre q1 (emisor) y q2 (receptor)
qc.h(1)
qc.cx(1, 2)

qc.barrier()

# 3. Alice (emisor) entrelaza su qubit original (q0) con su mitad
#    del par entrelazado (q1), y mide ambos
qc.cx(0, 1)
qc.h(0)
qc.measure(0, 0)
qc.measure(1, 1)

qc.barrier()

# 4. Bob (receptor) aplica correcciones a q2 según los resultados
#    clásicos que midió Alice (esto se llama "dynamic circuit":
#    la corrección depende del resultado de la medición, en tiempo real)
with qc.if_test((cr[1], 1)):
    qc.x(2)
with qc.if_test((cr[0], 1)):
    qc.z(2)

# 5. Medimos el qubit receptor para comprobar que el estado llegó
qc.measure(2, 2)

print(qc.draw())

# ============================================================
# EJECUTAR EN HARDWARE REAL
# ============================================================

# Buscamos un backend real que soporte "dynamic circuits"
# (necesarios para el if_test de arriba)
backend = service.least_busy(
    operational=True,
    simulator=False,
    dynamic_circuits=True
)
print("Usando:", backend.name)

from qiskit import transpile
qc_transpilado = transpile(qc, backend)

sampler = Sampler(backend)
job = sampler.run([qc_transpilado], shots=1000)
print("Job enviado, esperando resultado (puede tardar por la cola)...")

result = job.result()
conteos = result[0].data.c.get_counts()

print()
print("Resultados completos (3 bits: c2 c1 c0):")
print(conteos)

# ============================================================
# INTERPRETAR: nos interesa solo el bit del qubit receptor (c2,
# el primer carácter de cada llave, según convención de Qiskit)
# ============================================================
receptor_0 = sum(v for k, v in conteos.items() if k[0] == "0")
receptor_1 = sum(v for k, v in conteos.items() if k[0] == "1")
total = receptor_0 + receptor_1

print()
print(f"Qubit receptor midió 0: {receptor_0} veces ({receptor_0/total*100:.1f}%)")
print(f"Qubit receptor midió 1: {receptor_1} veces ({receptor_1/total*100:.1f}%)")
