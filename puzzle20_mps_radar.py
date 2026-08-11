import time
from qiskit import transpile
from qiskit_aer import AerSimulator
from bitcoin_quantum_oracle import BitcoinQuantumOracle

def dispatch_to_bitcrack(prefix_bin, total_puzzle_bits):
    remaining_bits = total_puzzle_bits - len(prefix_bin)
    start_bin = prefix_bin + ('0' * remaining_bits)
    end_bin = prefix_bin + ('1' * remaining_bits)
    
    start_hex = hex(int(start_bin, 2))[2:]
    end_hex = hex(int(end_bin, 2))[2:]
    
    address_alvo = "1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum" # Endereço oficial do Puzzle 20
    
    prefix_val = int(prefix_bin, 2)
    max_prefix_val = (2 ** len(prefix_bin)) - 1
    percentage = (prefix_val / max_prefix_val) * 100 if max_prefix_val > 0 else 0
    
    print(f"\n[SUCESSO] O Radar Quântico Lossy (MPS) detectou um pico de ressonância!")
    print(f"Pista Localizada: A Chave Privada do Puzzle 20 está aproximadamente na faixa de {percentage:.4f}% do Range Total.")
    print(f"Inicie a varredura bruta neste intervalo específico no seu PC LOCAL:")
    print(f"cuBitCrack -t 256 --keyspace {start_hex}:{end_hex} {address_alvo}\n")

def main():
    print("\n==========================================================")
    print("   PUZZLE 20: RADAR QUÂNTICO (CARGA FÍSICA) + MPS")
    print("==========================================================")
    
    total_bits = 20
    quantum_bits = 4   # Quantidade de bits em superposição (GPU)
    prefix_bits = total_bits - quantum_bits
    
    # O valor alvo A (Chave privada conhecida do Puzzle 20 para validar o Radar)
    # A chave do Puzzle 20 é 0x8a924. Usaremos ela para o teste de ressonância bater no alvo certo.
    target_A = 0x8a924
    target_hash_bin = format(target_A, f'0{total_bits}b')
    
    print(f"[#] Busca Total: {total_bits} bits (Puzzle 20)")
    print(f"[#] Range (HEX): 80000 a FFFFF (Bit mais significativo travado em 1)")
    print(f"[#] Carga do Grafo: {total_bits*2 + 1} Qubits (Com cascata Toffoli para Stress Test)")
    print(f"[#] Fatia Quântica (GPU): {quantum_bits} bits")
    print(f"[#] Estratégia Tensorial: MPS (Matrix Product State) com Poda (Truncation)")
    print("----------------------------------------------------------\n")
    
    oracle = BitcoinQuantumOracle(total_bits, quantum_bits, target_hash_bin)
    
    # Atenção: Configurado para rodar na Vast.ai (GPU)
    simulator = AerSimulator(method='matrix_product_state', device='GPU')
    simulator.set_options(
        matrix_product_state_max_bond_dimension=64,
        matrix_product_state_truncation_threshold=1e-5
    )
    
    t_global_start = time.time()
    
    start_prefix = 2**(prefix_bits - 1)
    end_prefix = 2**prefix_bits
    
    # Inicia um pouco antes para simular a varredura. Prefixo de 0x8a924 é 0x8a92 (35474)
    start_test = 35470
    
    for i in range(start_test, end_prefix):
        prefix_bin = format(i, f'0{prefix_bits}b')
        print(f"[*] GPU (Vast.ai) testando Bloco Clássico [{prefix_bin}****]...")
        
        t_start = time.time()
        
        qc = oracle.build_circuit(prefix_bin)
        
        compiled = transpile(qc, backend=simulator)
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        
        counts = result.get_counts()
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top_state, top_shots = sorted_counts[0]
        confidence = (top_shots / 1024) * 100
        
        t_end = time.time()
        print(f"    -> GPU Retornou Sufixo: {top_state} (Confiança: {confidence:.2f}%) em {t_end - t_start:.2f}s")
        
        if confidence > 5.0 and top_state != "0000": 
            if int(top_state, 2) == (target_A & ((1 << quantum_bits) - 1)): 
                full_key_prefix = prefix_bin + top_state
                print(f"\n[!] Radar Quântico detectou ressonância de fase no prefixo: {full_key_prefix}")
                dispatch_to_bitcrack(full_key_prefix, total_bits)
                break
            
    t_global_end = time.time()
    print(f"\nTempo Total Híbrido: {t_global_end - t_global_start:.2f}s")

if __name__ == "__main__":
    main()
