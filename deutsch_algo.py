import numpy as np

# Definición de puertas
H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
I = np.eye(2, dtype=complex)

def deutsch_oracle(tipo):
    """Crea una matriz de 4x4 que representa la función f(x)
    El oráculo cuántico mapea |x>|y> -> |x>|y ^ f(x)>
    """
    if tipo == 'constante_0': # f(x) = 0
        return np.eye(4, dtype=complex)
    elif tipo == 'constante_1': # f(x) = 1
        # Flip segundo qubit: X aplicado al segundo qubit
        return np.kron(I, np.array([[0,1],[1,0]], dtype=complex))
    elif tipo == 'balanceada_identidad': # f(x) = x
        # CNOT: si primer qubit es 1, flip segundo
        return np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)
    elif tipo == 'balanceada_not': # f(x) = NOT x
        # CNOT seguido de X en el segundo qubit
        CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)
        X_second = np.kron(I, np.array([[0,1],[1,0]], dtype=complex))
        return X_second @ CNOT

def run_deutsch(tipo):
    # Estado inicial |01>
    # Qubit 0: |0>, Qubit 1: |1>
    psi = np.array([0, 1, 0, 0], dtype=complex)
    
    # 1. Aplicar Hadamard a ambos qubits
    psi = np.kron(H, H) @ psi
    
    # 2. Aplicar el Oráculo (f)
    psi = deutsch_oracle(tipo) @ psi
    
    # 3. Aplicar Hadamard al primer qubit
    psi = np.kron(H, I) @ psi
    
    # 4. Medir el primer qubit
    # Probabilidad de obtener |0> vs |1>
    # Si obtenemos |0> -> Constante, Si |1> -> Balanceada
    # El primer qubit está en psi[0] o psi[1]
    prob_0 = np.abs(psi[0])**2 + np.abs(psi[1])**2
    return "Constante" if prob_0 > 0.5 else "Balanceada"

tipos = ['constante_0', 'constante_1', 'balanceada_identidad', 'balanceada_not']
for t in tipos:
    print(f"Tipo de función: {t:20} -> Resultado cuántico: {run_deutsch(t)}")
