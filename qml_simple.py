#!/usr/bin/env python3
import math, random

def neurona_cuantica(x, peso):
    """
    1. Entrada (x) + Peso aprendible (peso) -> Ángulo de rotación theta.
    2. Modifica la probabilidad de colapsar en |0> o |1>.
    """
    theta = x * peso
    
    # Amplitudes del qúbit tras la rotación (Matriz RY)
    amp_0 = math.cos(theta / 2)
    amp_1 = math.sin(theta / 2)
    
    # Probabilidad de medir el estado |1>
    prob_1 = amp_1 ** 2
    return prob_1

def entrenar():
    print("🧠 --- ENTRENANDO RED NEURONAL CUÁNTICA EN PYTHON --- 🧠\n")
    
    # Datos de entrenamiento: Entrada X -> Queremos que aprenda la Salida Y
    datos = [
        {"x": 1.0, "y": 1.0},
        {"x": 0.0, "y": 0.0}
    ]
    
    peso = random.uniform(0.1, 1.0) # Peso inicial aleatorio
    tasa_aprendizaje = 0.5
    
    print(f"Peso inicial aleatorio: {peso:.4f}\n")
    
    # Bucle de aprendizaje (Epochs / Épocas)
    for epoca in range(1, 21):
        error_total = 0
        
        for d in datos:
            # 1. Pase hacia adelante (Forward): Predicción cuántica
            prediccion = neurona_cuantica(d["x"], peso)
            
            # 2. Calcular error (Diferencia entre lo real y lo predicho)
            error = d["y"] - prediccion
            error_total += abs(error)
            
            # 3. Ajuste de peso mediante Gradiente Descendente
            peso += tasa_aprendizaje * error * d["x"]
            
        if epoca % 5 == 0 or epoca == 1:
            print(f"Época {epoca:2d} | Error: {error_total:.4f} | Peso ajustado: {peso:.4f}")

    print("\n✅ ENTRENAMIENTO COMPLETO")
    print(f"Peso final optimizado: {peso:.4f}\n")
    
    # Prueba del modelo entrenado
    print("--- PRUEBA DE PREDICCIÓN ---")
    for d in datos:
        pred = neurona_cuantica(d["x"], peso)
        resultado = 1 if pred > 0.5 else 0
        print(f"Entrada: {d['x']} -> Probabilidad cuántica de |1>: {pred:.2%} | Clase: {resultado}")

if __name__ == "__main__":
    entrenAR = entrenar()
