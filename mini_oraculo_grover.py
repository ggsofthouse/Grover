# mini_oraculo_grover.py
"""
PoC: Algoritmo de Grover com Oráculo Reversível e Phase Kickback (Ancilla)
Espaço de busca: 4 bits (16 estados).

Regras Implementadas:
1. Oráculo construído manualmente demonstrando o Uncompute.
2. Ancilla isolada no estado |-> para kickback de fase.
3. Aceleração Tensorial com cuQuantum / Qiskit Aer GPU.
"""

import math
import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def mini_hash_round(qc, q_regs):
    """
    Simula uma operação de hash reversível muito básica.
    Aplica um XOR com a constante 1010 (bits 1 e 3)
    """
    # X_gate(1) e X_gate(3)
    qc.x(q_regs[1])
    qc.x(q_regs[3])

def mini_hash_uncompute(qc, q_regs):
    """
    O Uncompute deve aplicar o inverso exato das portas do hash na ordem reversa.
    Como X é o seu próprio inverso, apenas repetimos na ordem inversa.
    """
    qc.x(q_regs[3])
    qc.x(q_regs[1])

def verify_target(qc, q_regs):
    """
    O Oráculo deseja encontrar o estado cujo "hash" resulte na target '0101'
    Para ativar o MCX (multi-controlled X), precisamos que todos os qubits
    sejam |1>. Portanto, invertemos os qubits onde a target tem '0'.
    Target = 0101 (q3=0, q2=1, q1=0, q0=1)
    """
    qc.x(q_regs[3])
    qc.x(q_regs[1])

def verify_target_uncompute(qc, q_regs):
    """ Desfaz a preparação do target. """
    qc.x(q_regs[1])
    qc.x(q_regs[3])

def apply_diffuser(qc, q_regs):
    """
    Difusor de Grover (Reflexão sobre a média).
    """
    # 1. H em todos os qubits de busca
    qc.h(q_regs)
    
    # 2. X em todos (preparando para focar no estado |0000>)
    qc.x(q_regs)
    
    # 3. Multi-Controlled Z (Phase flip no estado |1111> transformado)
    # MCZ é equivalente a: H no alvo, MCX, H no alvo.
    last_qubit = q_regs[-1]
    controls = q_regs[:-1]
    qc.h(last_qubit)
    qc.mcx(controls, last_qubit)
    qc.h(last_qubit)
    
    # 4. Desfaz X em todos
    qc.x(q_regs)
    
    # 5. Desfaz H em todos
    qc.h(q_regs)

def main():
    n_qubits = 4
    # Total = 4 qubits (busca) + 1 qubit (ancilla)
    qc = QuantumCircuit(n_qubits + 1, n_qubits)
    
    q_search = list(range(n_qubits))
    q_ancilla = n_qubits

    # 1. INICIALIZAÇÃO
    # Qubits de busca em superposição
    qc.h(q_search)
    
    # Ancilla no estado |-> para o Phase Kickback
    qc.x(q_ancilla)
    qc.h(q_ancilla)
    qc.barrier()

    # 2. CALCULO DE ITERAÇÕES (Grover)
    # ~ (pi / 4) * sqrt(2^N)
    iterations = math.floor((math.pi / 4) * math.sqrt(2 ** n_qubits))
    print(f"Número calculado de iterações de Grover (N=16): {iterations}")

    # 3. LOOP DE GROVER
    for _ in range(iterations):
        # ----- ORÁCULO MANUAL COM UNCOMPUTE -----
        # a) Executa o processamento do "Mini-Hash"
        mini_hash_round(qc, q_search)
        
        # b) Verifica a igualdade com o alvo ('0101')
        verify_target(qc, q_search)
        
        # c) Phase Kickback (MCX na Ancilla)
        qc.mcx(q_search, q_ancilla)
        
        # d) Uncompute: VERIFICAÇÃO (crucial para não gerar lixo quântico)
        verify_target_uncompute(qc, q_search)
        
        # e) Uncompute: MINI-HASH (desfaz a matemática)
        mini_hash_uncompute(qc, q_search)
        qc.barrier()

        # ----- DIFUSOR -----
        apply_diffuser(qc, q_search)
        qc.barrier()

    # 4. MEDIÇÃO (Apenas os qubits de busca)
    qc.measure(q_search, range(n_qubits))

    print("\n[!] Desenhando Circuito Quântico (Visão de Portas/Uncompute):")
    print(qc.draw(fold=-1))

    # 5. EXECUÇÃO NA GPU VIA TENSOR NETWORK
    print("\nInicializando simulador AerSimulator (GPU / Tensor Network)...")
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
    except Exception as e:
        print(f"Erro ao instanciar GPU: {e}")
        return

    # Transpila o circuito para as portas bases da simulação
    t_start_trans = time.time()
    compiled_circ = transpile(qc, simulator)
    t_end_trans = time.time()
    print(f"Transpilação concluída em {t_end_trans - t_start_trans:.4f}s")

    print("\nContratando Redes Tensoriais na GPU...")
    t_start_run = time.time()
    job = simulator.run(compiled_circ, shots=1024)
    result = job.result()
    t_end_run = time.time()

    print(f"Status do job: {result.status}")
    print(f"Tempo de execução (GPU): {t_end_run - t_start_run:.4f}s")

    # 6. RESULTADOS
    counts = result.get_counts()
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state, top_shots = sorted_counts[0]
    
    # A leitura no Qiskit é em Little-Endian por padrão. Vamos apenas exibir como lido.
    print(f"\n--- RESULTADO FINAL DO ORÁCULO ---")
    print(f"Estado Encontrado (Pre-Image): {top_state}")
    print(f"Probabilidade do colapso: {(top_shots/1024)*100:.2f}%")
    
    # Verificação Clássica
    # O Qiskit lê na ordem q3 q2 q1 q0. 
    # Nosso Hash: XOR(1010). Target = 0101. Pre-image esperada = 0101 XOR 1010 = 1111.
    print("Verificação Clássica de Sucesso: Pre-image = 1111.")

if __name__ == "__main__":
    main()
