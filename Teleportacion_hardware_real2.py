from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import numpy as np

# ============================================================
# CONFIGURA TU TOKEN AQUÍ
# ============================================================
TOKEN = "kaWOqgYrr_hYzvGTIYeMasRmrPRHFnj2ZlRwBMGasTLm"

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN)
# ============================================================
# GROVER: buscar el estado |101> entre 8 posibilidades (3 qubits)
# ============================================================
# Igual que en tu Mini-Qiskit: objetivo = 101
# ============================================================

N_QUBITS = 3
OBJETIVO = "101"  # el estado que queremos encontrar


def oraculo(qc, objetivo):
    """
    Invierte la fase del estado objetivo.
    Truco: aplicamos X a los qubits donde el objetivo tiene un '0',
    así el objetivo queda representado como |111>, aplicamos una
    puerta Z multi-controlada (CCZ), y deshacemos las X.
    """
    for i, bit in enumerate(reversed(objetivo)):
        if bit == "0":
            qc.x(i)

    qc.h(N_QUBITS - 1)
    qc.mcx(list(range(N_QUBITS - 1)), N_QUBITS - 1)  # CCX multicontrolada
    qc.h(N_QUBITS - 1)

    for i, bit in enumerate(reversed(objetivo)):
        if bit == "0":
            qc.x(i)


def difusor(qc):
    """Operador de difusión estándar de Grover."""
    qc.h(range(N_QUBITS))
    qc.x(range(N_QUBITS))

    qc.h(N_QUBITS - 1)
    qc.mcx(list(range(N_QUBITS - 1)), N_QUBITS - 1)
    qc.h(N_QUBITS - 1)

    qc.x(range(N_QUBITS))
    qc.h(range(N_QUBITS))


qc = QuantumCircuit(N_QUBITS, N_QUBITS)

# Superposición inicial
qc.h(range(N_QUBITS))

# Iteraciones óptimas para 3 qubits (8 estados) = 2
iteraciones = round((np.pi / 4) * np.sqrt(2 ** N_QUBITS))

for _ in range(iteraciones):
    oraculo(qc, OBJETIVO)
    difusor(qc)

qc.measure(range(N_QUBITS), range(N_QUBITS))

print(qc.draw())
print(f"\nIteraciones de Grover: {iteraciones}")

# ============================================================
# EJECUTAR EN HARDWARE REAL
# ============================================================

backend = service.least_busy(operational=True, simulator=False)
print("Usando:", backend.name)

qc_transpilado = transpile(qc, backend)

sampler = Sampler(backend)
job = sampler.run([qc_transpilado], shots=1000)
print("Job enviado, esperando resultado (puede tardar por la cola)...")

result = job.result()
conteos = result[0].data.c.get_counts()

print()
print("Resultados completos:")
for estado, cuenta in sorted(conteos.items(), key=lambda x: -x[1]):
    marca = "  <-- objetivo" if estado == OBJETIVO else ""
    print(f"  |{estado}> -> {cuenta} veces ({cuenta/10:.1f}%){marca}")
