from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# Conectar con tu cuenta
service = QiskitRuntimeService(channel="ibm_quantum_platform", token="kaWOqgYrr_hYzvGTIYeMasRmrPRHFnj2ZlRwBMGasTLm")

# Circuito Bell real
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# Elegir un computador cuántico real disponible
backend = service.least_busy(operational=True, simulator=False)
print("Usando:", backend.name)

# Transpilar el circuito a un circuito ISA (Instruction Set Architecture) compatible con el hardware
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
isa_qc = pm.run(qc)

# Ejecutar
sampler = Sampler(backend)
job = sampler.run([isa_qc], shots=1000)
result = job.result()
print(result[0].data.c.get_counts())
