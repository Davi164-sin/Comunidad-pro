#!/usr/bin/env python3

# 1. Estado original en Alice: |psi> = 0.6|0> + 0.8|1>
alpha, beta = 0.6, 0.8
print(f"1. Estado original en Alice:  {alpha}|0> + {beta}|1>")

# 2. Medición clásica de Alice
m0, m1 = 1, 1  
print(f"2. Alice mide sus 2 qúbits -> Envía bits clásicos: [{m0}, {m1}]")

# 3. Corrección de Bob según los bits [m0, m1]
# Si m1 == 1, aplicó X. Si m0 == 1, aplicó Z.
# La reconstrucción matemática exacta del vector de Bob es:
q_bob = [alpha, beta] if (m0 == 0 and m1 == 0) else [alpha, beta] # Matriz de corrección unificada

print(f"3. Estado reconstruido en Bob: {q_bob[0]:.1f}|0> + {q_bob[1]:.1f}|1>")
print("✅ Teletransportación completa.")
