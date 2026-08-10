# grover_mini_oracle.py
"""
Prova de Conceito (PoC) do Algoritmo de Grover com Oráculo Reversível
Acelerado via cuTensorNet / Qiskit Aer GPU na RTX 2060.
"""

import math
import time
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import MCMT, ZGate
from qiskit_aer import AerSimulator

def create_oracle(n_qubits: int, target_bitstring: str) -> QuantumCircuit:
    """
    Cria um Oráculo Quântico de Inversão de Fase (-1) para a chave alvo.
    Chave alvo em formato binário string de tamanho n_qubits.
    """
    qc = QuantumCircuit(n_qubits, name="Oracle")
    
    # 1. Flip nos qubits onde a chave alvo é '0'
    for i, bit in enumerate(target_bitstring[::-1]):
        if bit == '0':
            qc.x(i)
            
    # 2. Multi-Controlled Z Gate (inverte a fase do estado |11...1>)
    if n_qubits == 1:
        qc.z(0)
    else:
        # Porta Z multi-controlada nos n-1 primeiros qubits atuando no último
        qc.h(n_qubits - 1)
        qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        qc.h(n_qubits - 1)

    # 3. Uncompute os X gates para restaurar o estado base
    for i, bit in enumerate(target_bitstring[::-1]):
        if bit == '0':
            qc.x(i)
            
    return qc

def create_diffuser(n_qubits: int) -> QuantumCircuit:
    """
    Cria o Difusor de Grover (Reflexão sobre a Média: 2|s><s| - I).
    """
    qc = QuantumCircuit(n_qubits, name="Diffuser")
    
    # Superposição invertida
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))
    
    # Inversão de fase no estado |00...0>
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    qc.h(n_qubits - 1)
    
    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    
    return qc

def run_grover_poc(n_qubits: int = 12, target_bitstring: str = "101101001101"):
    assert len(target_bitstring) == n_qubits, "Tamanho da string da chave deve ser igual a n_qubits"
    print(f"\n========================================================")
    print(f"   Executando Grover PoC | N = {n_qubits} Qubits ({2**n_qubits} estados)")
    print(f"   Chave Alvo: {target_bitstring}")
    print(f"========================================================")

    # Calcular número ideal de iterações de Grover: ~ (pi / 4) * sqrt(2^N)
    N_states = 2**n_qubits
    iterations = max(1, int(math.floor((math.pi / 4) * math.sqrt(N_states))))
    print(f"Iterações do Oráculo + Difusor calculadas: {iterations}")

    # Montar circuito principal
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # Passo 1: Superposição inicial total
    qc.h(range(n_qubits))
    
    # Passo 2 & 3: Loop do Oráculo + Difusor
    oracle = create_oracle(n_qubits, target_bitstring)
    diffuser = create_diffuser(n_qubits)
    
    for it in range(iterations):
        qc.append(oracle, range(n_qubits))
        qc.append(diffuser, range(n_qubits))
        
    qc.measure(range(n_qubits), range(n_qubits))

    print("\nInicializando simulador Qiskit Aer GPU cuTensorNet...")
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
    except Exception as e:
        print(f"Erro ao inicializar AerSimulator GPU: {e}")
        return

    print("Transpilando circuito quântico...")
    t_start_transpile = time.time()
    compiled_circuit = transpile(qc, simulator)
    t_end_transpile = time.time()
    print(f"Tempo de transpilação: {t_end_transpile - t_start_transpile:.4f}s")

    print(f"Executando simulação de Rede Tensorial na GPU RTX 2060 (Shots: 1024)...")
    t_start_run = time.time()
    job = simulator.run(compiled_circuit, shots=1024)
    result = job.result()
    t_end_run = time.time()

    counts = result.get_counts()
    print(f"Tempo de execução do contrato de tensores na GPU: {t_end_run - t_start_run:.4f}s")
    
    # Ordenar resultados por frequência de medição
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_result, top_shots = sorted_counts[0]
    prob = (top_shots / 1024.0) * 100

    print("\n--- RESULTADOS DA SIMULAÇÃO QUÂNTICA ---")
    print(f"Estado mais medido: {top_result} ({top_shots}/1024 shots -> {prob:.2f}% de probabilidade)")
    print(f"Chave Alvo Esperada: {target_bitstring}")
    
    if top_result == target_bitstring:
        print("SUCCESS: A amplitude quântica colapsou com sucesso na chave exata via Grover!")
    else:
        print("AVISO: O estado mais medido difere da chave alvo.")

if __name__ == "__main__":
    # Teste inicial com 12 qubits (4096 combinações)
    run_grover_poc(n_qubits=12, target_bitstring="101101001101")
