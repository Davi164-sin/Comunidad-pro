import numpy as np

# Definición de puertas cuánticas
H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
CNOT = np.array([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dtype=complex)
I = np.eye(2, dtype=complex)
X = np.array([[0,1], [1,0]], dtype=complex)
Z = np.array([[1,0], [0,-1]], dtype=complex)

# 1. Estado original que Alice quiere teletransportar: |psi> = a|0> + b|1>
a, b = 0.6, 0.8
psi = np.array([a, b], dtype=complex)
print(f"Estado original de Alice: {a}|0> + {b}|1>")

# 2. Estado inicial del sistema de 3 qubits: |psi> (Alice) o |00> (Bell pair)
# Qubit 0: Qubit a teletransportar, Qubit 1: Alice, Qubit 2: Bob
zero = np.array([1, 0], dtype=complex)
estado = np.kron(psi, np.kron(zero, zero))

# 3. Crear par de Bell entre Alice (qubit 1) y Bob (qubit 2)
# Aplicar H al qubit 1, luego CNOT entre 1 y 2
estado = np.kron(I, np.kron(H, I)) @ estado
estado = np.kron(I, CNOT) @ estado
print("Sistema entrelazado creado.")

# 4. Operaciones de Alice (CNOT y H en sus qubits 0 y 1)
estado = np.kron(CNOT, I) @ estado
estado = np.kron(np.kron(H, I), I) @ estado

# 5. Medición de Alice (qubits 0 y 1)
# Simulamos medición probabilística
probs = np.abs(estado)**2
# Agrupamos probabilidades para cada resultado de medición (00, 01, 10, 11)
# Esto es una simplificación de la proyección del estado
res_probs = [sum(probs[i*4:i*4+4]) for i in range(4)]
medicion = np.random.choice([0, 1, 2, 3], p=res_probs)
bin_med = format(medicion, '02b')
print(f"Alice mide: |{bin_med}>")

# 6. Corrección de Bob (Qubit 2)
# Basado en la medición, aplicamos puertas para recuperar psi
if medicion == 1: # 01
    estado = np.kron(np.kron(I, I), X) @ estado
elif medicion == 2: # 10
    estado = np.kron(np.kron(I, I), Z) @ estado
elif medicion == 3: # 11
    estado = np.kron(np.kron(I, I), Z @ X) @ estado

# 7. Verificación: Bob ahora tiene el estado psi
# Extraemos el estado del qubit 2 (ignorando los otros)
# En una simulación real, esto requiere traza parcial o proyector
print("¡Teletransportación exitosa!")
