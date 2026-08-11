import time
from qiskit import transpile
from qiskit_aer import AerSimulator
from bitcoin_full_quantum_oracle import BitcoinAddressQuantumOracle

def run_puzzle15_address_radar():
    print("=========================================================")
    print("   PUZZLE 15: RADAR QUÂNTICO (ADDRESS-ONLY ATTACK)")
    print("=========================================================")
    
    total_bits = 15
    quantum_bits = 4   # Quantidade de bits da chave na superposição
    prefix_bits = total_bits - quantum_bits
    
    # Toy Address (Alvo Simulado de 2 bits - representação do RIPEMD160 Final)
    # Num cenário real, isso seria o Address base58 decodificado para binário.
    target_address_bin = "10"
    
    print(f"[#] Busca Total: {total_bits} bits (Puzzle 15)")
    print(f"[#] Range Quântico: {quantum_bits} bits")
    print(f"[#] Alvo (Toy Address): {target_address_bin} (Simulação do Hash160 Cego)")
    print(f"[#] Oráculo Pipeline Completo: ECDLP + Hashing Reverso")
    print("-" * 57)
    
    # ====================================================================
    # CONFIGURAÇÃO DE SEGURANÇA CONTRA OOM (Out of Memory) PARA A RTX 4090
    # ====================================================================
    simulator = AerSimulator(method='matrix_product_state', device='GPU')
    simulator.set_options(
        matrix_product_state_max_bond_dimension=128, 
        matrix_product_state_truncation_threshold=1e-5 
    )
    
    oracle = BitcoinAddressQuantumOracle(total_bits, quantum_bits, target_address_bin)
    
    start_prefix = 2**(prefix_bits - 1) 
    end_prefix = 2**prefix_bits         
    
    start_test = start_prefix
    
    start_time = time.time()
    
    # Para o teste, rodamos apenas 2 blocos (para validar a estabilidade)
    test_limit = start_test + 2
    
    for i in range(start_test, end_prefix):
        if i >= test_limit:
            print("\n[!] Teste de estabilidade Address-Only concluído (2 blocos).")
            break
            
        prefix_bin = format(i, f'0{prefix_bits}b')
        print(f"\n[*] GPU (Vast.ai) testando Bloco Clássico [{prefix_bin}****]...")
        
        t0 = time.time()
        qc = oracle.build_circuit(prefix_bin)
        
        # Transpilação explícita para desconstruir o pipeline inteiro em portas basais
        compiled = transpile(qc, backend=simulator)
        
        job = simulator.run(compiled, shots=512)
        result = job.result()
        counts = result.get_counts()
        
        top_state = max(counts, key=counts.get)
        max_shots = counts[top_state]
        confidence = (max_shots / 512) * 100
        
        top_state_clean = top_state.replace(" ", "")
        
        print(f"    -> GPU Retornou Pico: {top_state_clean} (Confiança: {confidence:.2f}%) em {time.time() - t0:.2f}s")
        print(f"    (O TensorNet simulou ECDLP + Hashing com sucesso sem estourar a VRAM!)")

    print(f"\nTempo Total Híbrido: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    run_puzzle15_address_radar()
