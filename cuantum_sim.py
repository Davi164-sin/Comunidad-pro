import numpy as np
from collections import Counter


# ============================================================
# SIMULADOR CUÁNTICO DESDE CERO
# ============================================================

class QuantumSimulator:

    def __init__(self, num_qubits):
        self.n = num_qubits
        self.size = 2 ** num_qubits

        # Estado inicial |00...0>
        self.state = np.zeros(self.size, dtype=complex)
        self.state[0] = 1.0

    # --------------------------------------------------------
    # MATRICES DE PUERTAS
    # --------------------------------------------------------

    X = np.array([
        [0, 1],
        [1, 0]
    ], dtype=complex)

    Y = np.array([
        [0, -1j],
        [1j, 0]
    ], dtype=complex)

    Z = np.array([
        [1, 0],
        [0, -1]
    ], dtype=complex)

    H = (1 / np.sqrt(2)) * np.array([
        [1, 1],
        [1, -1]
    ], dtype=complex)

    # --------------------------------------------------------
    # PUERTA DE UN QUBIT
    # --------------------------------------------------------

    def gate(self, matrix, target):
        """
        Aplica una puerta a un qubit concreto.
        target = 0, 1, 2...
        """

        new_state = np.zeros_like(self.state)

        for i in range(self.size):

            bit = (i >> target) & 1

            # Índice con el bit objetivo cambiado
            j = i ^ (1 << target)

            if bit == 0:
                new_state[i] += matrix[0, 0] * self.state[i]
                new_state[j] += matrix[1, 0] * self.state[i]

            else:
                new_state[j] += matrix[0, 1] * self.state[i]
                new_state[i] += matrix[1, 1] * self.state[i]

        self.state = new_state

    # --------------------------------------------------------
    # CONTROLLED-X / CNOT
    # --------------------------------------------------------

    def cnot(self, control, target):

        new_state = self.state.copy()

        for i in range(self.size):

            control_bit = (i >> control) & 1

            if control_bit == 1:
                j = i ^ (1 << target)

                new_state[j] = self.state[i]

        self.state = new_state

    # --------------------------------------------------------
    # MEDICIÓN
    # --------------------------------------------------------

    def measure(self):

        probabilities = np.abs(self.state) ** 2

        result = np.random.choice(
            self.size,
            p=probabilities
        )

        binary = format(result, f"0{self.n}b")

        return binary

    # --------------------------------------------------------
    # MOSTRAR ESTADO
    # --------------------------------------------------------

    def show_state(self):

        print("\nEstado cuántico:")

        for i, amplitude in enumerate(self.state):

            probability = abs(amplitude) ** 2

            if probability > 1e-10:

                binary = format(i, f"0{self.n}b")

                print(
                    f"|{binary}> "
                    f"amplitud = {amplitude:.4f} "
                    f"probabilidad = {probability * 100:.2f}%"
                )

    # --------------------------------------------------------
    # SHOTS
    # --------------------------------------------------------

    def run(self, shots=1000):

        results = []

        probabilities = np.abs(self.state) ** 2

        for _ in range(shots):

            result = np.random.choice(
                self.size,
                p=probabilities
            )

            binary = format(result, f"0{self.n}b")

            results.append(binary)

        return Counter(results)


# ============================================================
# EXPERIMENTO 1
# SUPERPOSICIÓN
# ============================================================

print("=" * 60)
print("EXPERIMENTO 1: SUPERPOSICIÓN")
print("=" * 60)

q = QuantumSimulator(1)

q.gate(q.H, 0)

q.show_state()

print("\n1000 mediciones:")

results = q.run(1000)

print(results)


# ============================================================
# EXPERIMENTO 2
# ENTRELAZAMIENTO - BELL STATE
# ============================================================

print("\n")
print("=" * 60)
print("EXPERIMENTO 2: ENTRELAZAMIENTO CUÁNTICO")
print("=" * 60)

q = QuantumSimulator(2)

# |00>
# H en q0
q.gate(q.H, 0)

# CNOT
q.cnot(0, 1)

q.show_state()

print("\n1000 mediciones:")

results = q.run(1000)

print(results)


# ============================================================
# EXPERIMENTO 3
# GROVER SIMPLE
# ============================================================

print("\n")
print("=" * 60)
print("EXPERIMENTO 3: GROVER")
print("=" * 60)

q = QuantumSimulator(2)

# Crear superposición
q.gate(q.H, 0)
q.gate(q.H, 1)

print("\nSuperposición inicial:")
q.show_state()

# ------------------------------------------------------------
# Oráculo: marcar |11>
# ------------------------------------------------------------

for i in range(len(q.state)):

    if i == 3:
        q.state[i] *= -1


# ------------------------------------------------------------
# Difusión de Grover
# ------------------------------------------------------------

media = np.mean(q.state)

q.state = 2 * media - q.state

print("\nDespués del algoritmo de Grover:")

q.show_state()

print("\n1000 mediciones:")

results = q.run(1000)

print(results)


# ============================================================
# FIN
# ============================================================

print("\n")
print("=" * 60)
print("SIMULACIÓN TERMINADA")
print("=" * 60)
