#!/usr/bin/env python3
"""
CÓDIGO DE CORRECCIÓN DE ERRORES CUÁNTICOS: BIT-FLIP DE 3 QUBITS
==================================================================

Simula, con un vector de estado completo (5 qubits = 32 dimensiones),
el código más simple de corrección de errores cuánticos:

  - 3 qubits de DATOS (q0, q1, q2): protegen 1 qubit lógico
  - 2 qubits ANCILLA (q3, q4): miden el "síndrome" del error, es decir,
    qué pasó, SIN revelar (ni destruir) el valor lógico protegido.

Flujo:
  1. Preparamos un estado arbitrario alpha|0> + beta|1> en q0 (el
     qubit lógico que queremos proteger).
  2. Lo codificamos en 3 qubits: alpha|000> + beta|111>
     (esto NO es clonar -- es entrelazar, el teorema de no-clonación
     sigue intacto).
  3. Simulamos un error de bit-flip (X) en UNO de los 3 qubits,
     elegido al azar (o ninguno).
  4. Medimos el síndrome con los 2 qubits ancilla -- esto nos dice
     CUÁL qubit falló, sin medir directamente los datos (y por lo
     tanto sin colapsar la superposición lógica).
  5. Aplicamos la corrección (X) al qubit indicado por el síndrome.
  6. Decodificamos y verificamos que el estado lógico original se
     recuperó, calculando la fidelidad.
"""

import numpy as np

np.random.seed(0)

N_QUBITS = 5  # q0,q1,q2 = datos | q3,q4 = ancillas


# ============================================================
# HERRAMIENTAS GENERALES DE SIMULACIÓN MULTI-QUBIT
# ============================================================

def bits_de(indice, n):
    return list(format(indice, f"0{n}b"))


def aplicar_puerta_1_qubit(estado, gate, qubit, n):
    """Aplica una puerta de 1 qubit (2x2) al qubit indicado."""
    I = np.eye(2, dtype=complex)
    op = np.array([[1]], dtype=complex)
    for q in range(n):
        op = np.kron(op, gate if q == qubit else I)
    return op @ estado


def aplicar_cnot(estado, control, target, n):
    """CNOT genérico entre dos qubits cualesquiera, en un sistema de n qubits."""
    N = 2 ** n
    nuevo = np.zeros_like(estado)
    for i in range(N):
        b = bits_de(i, n)
        if b[control] == "1":
            b[target] = "0" if b[target] == "1" else "1"
        j = int("".join(b), 2)
        nuevo[j] += estado[i]
    return nuevo


def medir_qubit(estado, qubit, n):
    """Mide un qubit específico, colapsando y renormalizando el estado."""
    N = 2 ** n
    prob0 = sum(
        abs(estado[i]) ** 2
        for i in range(N)
        if bits_de(i, n)[qubit] == "0"
    )
    resultado = 0 if np.random.rand() < prob0 else 1

    nuevo = np.zeros_like(estado)
    norma = 0.0
    for i in range(N):
        if bits_de(i, n)[qubit] == str(resultado):
            nuevo[i] = estado[i]
            norma += abs(estado[i]) ** 2
    nuevo /= np.sqrt(norma)
    return resultado, nuevo


X = np.array([[0, 1], [1, 0]], dtype=complex)


# ============================================================
# EXPERIMENTO: probar con y sin error, y con error en cada qubit
# ============================================================

def ejecutar_experimento(theta, error_en_qubit):
    """
    theta: ángulo que define el estado lógico a proteger
           (RY(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>)
    error_en_qubit: None, 0, 1 o 2 -- qué qubit de datos sufre bit-flip
    """
    n = N_QUBITS
    N = 2 ** n

    estado = np.zeros(N, dtype=complex)
    estado[0] = 1.0  # |00000>

    # --- 1. Preparar el estado lógico en q0 ---
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    RY = np.array([[c, -s], [s, c]], dtype=complex)
    estado = aplicar_puerta_1_qubit(estado, RY, 0, n)

    alpha, beta = c, s  # guardamos para comparar fidelidad al final

    # --- 2. Codificar: alpha|000> + beta|111> en q0,q1,q2 ---
    estado = aplicar_cnot(estado, 0, 1, n)
    estado = aplicar_cnot(estado, 0, 2, n)

    # --- 3. Simular un error de bit-flip ---
    if error_en_qubit is not None:
        estado = aplicar_puerta_1_qubit(estado, X, error_en_qubit, n)

    # --- 4. Extracción del síndrome con los ancillas q3, q4 ---
    #     q3 mide la paridad entre q0 y q1
    #     q4 mide la paridad entre q1 y q2
    estado = aplicar_cnot(estado, 0, 3, n)
    estado = aplicar_cnot(estado, 1, 3, n)
    estado = aplicar_cnot(estado, 1, 4, n)
    estado = aplicar_cnot(estado, 2, 4, n)

    s1, estado = medir_qubit(estado, 3, n)
    s2, estado = medir_qubit(estado, 4, n)

    # --- 5. Decodificar el síndrome y corregir ---
    mapa_sindrome = {
        (0, 0): None,  # sin error
        (1, 0): 0,     # error en q0
        (1, 1): 1,     # error en q1
        (0, 1): 2,     # error en q2
    }
    qubit_a_corregir = mapa_sindrome[(s1, s2)]

    if qubit_a_corregir is not None:
        estado = aplicar_puerta_1_qubit(estado, X, qubit_a_corregir, n)

    # --- 6. Decodificar (deshacer el entrelazamiento) y verificar ---
    estado = aplicar_cnot(estado, 0, 2, n)
    estado = aplicar_cnot(estado, 0, 1, n)

    # Tras decodificar, el estado debería ser (alpha|0> + beta|1>) en q0,
    # con q1,q2 de vuelta en |00>. Los ancillas (q3,q4) quedaron FIJOS
    # en el valor que se midió (s1, s2) -- no vuelven a 0 solos, porque
    # ya no se les aplica ninguna puerta después de medirlos.
    idx0 = int(f"0 00 {s1}{s2}".replace(" ", ""), 2)  # q0=0,q1=0,q2=0,q3=s1,q4=s2
    idx1 = int(f"1 00 {s1}{s2}".replace(" ", ""), 2)  # q0=1,q1=0,q2=0,q3=s1,q4=s2
    amp0 = estado[idx0]
    amp1 = estado[idx1]

    # Fidelidad respecto al estado original alpha|0>+beta|1>
    fidelidad = abs(alpha * np.conj(amp0) + beta * np.conj(amp1)) ** 2

    return s1, s2, qubit_a_corregir, fidelidad


# ============================================================
# CORRER PARA VARIOS CASOS
# ============================================================

theta = 1.9  # ángulo arbitrario -> alpha, beta no triviales

print("=" * 70)
print("  CÓDIGO DE CORRECCIÓN DE ERRORES (BIT-FLIP, 3 QUBITS)")
print("=" * 70)
print(f"\nEstado lógico preparado con theta = {theta} rad "
      f"(alpha={np.cos(theta/2):.3f}, beta={np.sin(theta/2):.3f})\n")

casos = [None, 0, 1, 2]
nombres = ["SIN error", "error en q0", "error en q1", "error en q2"]

for caso, nombre in zip(casos, nombres):
    s1, s2, corregido, fidelidad = ejecutar_experimento(theta, caso)
    corregido_str = f"q{corregido}" if corregido is not None else "ninguno"
    print(f"{nombre:14s} -> síndrome=({s1},{s2}) "
          f"-> corrige: {corregido_str:8s} -> fidelidad final: {fidelidad:.4f}")

print()
print("=" * 70)
print("  COMPARACIÓN: ¿QUÉ PASARÍA SIN CORRECCIÓN?")
print("=" * 70)


def ejecutar_sin_correccion(theta, error_en_qubit):
    n = N_QUBITS
    N = 2 ** n
    estado = np.zeros(N, dtype=complex)
    estado[0] = 1.0

    c, s = np.cos(theta / 2), np.sin(theta / 2)
    RY = np.array([[c, -s], [s, c]], dtype=complex)
    estado = aplicar_puerta_1_qubit(estado, RY, 0, n)
    alpha, beta = c, s

    estado = aplicar_cnot(estado, 0, 1, n)
    estado = aplicar_cnot(estado, 0, 2, n)

    if error_en_qubit is not None:
        estado = aplicar_puerta_1_qubit(estado, X, error_en_qubit, n)

    # decodificar SIN corregir el error
    estado = aplicar_cnot(estado, 0, 2, n)
    estado = aplicar_cnot(estado, 0, 1, n)

    # Aquí NO medimos los ancillas, así que pueden seguir en superposición.
    # Sumamos la probabilidad sobre las 4 combinaciones posibles de
    # ancilla para obtener la amplitud efectiva de q0=0 y q0=1.
    amp0 = sum(estado[int(f"0 00 {a}{b}".replace(' ', ''), 2)] for a in "01" for b in "01")
    amp1 = sum(estado[int(f"1 00 {a}{b}".replace(' ', ''), 2)] for a in "01" for b in "01")
    fidelidad = abs(alpha * np.conj(amp0) + beta * np.conj(amp1)) ** 2
    return fidelidad


for caso, nombre in zip(casos, nombres):
    fid = ejecutar_sin_correccion(theta, caso)
    print(f"{nombre:14s} -> fidelidad SIN corrección: {fid:.4f}")

print()
print("=" * 70)
print("  CONCLUSIÓN")
print("=" * 70)
print("""
Con el código de 3 qubits, la fidelidad se recupera a 1.0000 en los 4
casos (sin error, o con error en cualquiera de los 3 qubits), porque el
síndrome identifica exactamente cuál qubit falló y se corrige antes de
decodificar.

Sin corrección, un error de bit-flip en cualquiera de los 3 qubits
arruina completamente el estado lógico (fidelidad baja), porque el
decodificador (CNOTs inversos) asume que los 3 qubits siguen
correlacionados como al codificarlos.
""")
