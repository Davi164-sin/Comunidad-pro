import numpy as np

qubit = np.array([1, 0])

H = (1/np.sqrt(2)) * np.array([
    [1, 1],
    [1, -1]
])

resultado = H @ qubit

print("Estado inicial:", qubit)
print("Estado después de Hadamard:", resultado)

