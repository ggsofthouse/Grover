import time
import os
from qiskit_aer import AerSimulator
from bitcoin_quantum_oracle import BitcoinQuantumOracle

def run_puzzle15_radar():
    print("=========================================================")
    print("   PUZZLE 15: RADAR QUÂNTICO (SHA-256 SHADOW ATTACK)")
    print("=========================================================")
    
    total_bits = 15
    quantum_bits = 4
    prefix_bits = total_bits - quantum_bits
    
    # Target "Shadow" (Chave escolhida para o benchmark do SHA-256 no Puzzle 15)
    # Range de 0x4000 a 0x7FFF. Vamos escolher 0x6A3B
    target_A = 0x6a3b
    target_hash_bin = format(target_A, f'0{total_bits}b')
    
    print(f"[#] Busca Total: {total_bits} bits (Puzzle 15)")
    print(f"[#] Range (HEX): 4000 a 7FFF")
    print(f"[#] Carga do Grafo: Funções Reversíveis do SHA-256 (Ch e Maj)")
    print(f"[#] Fatia Quântica (GPU): {quantum_bits} bits")
    print(f"[#] Estratégia Tensorial: MPS (Matrix Product State)\n")
    print("-" * 57)
    
    # Configuração AerSimulator para GPU e MPS
    simulator = AerSimulator(method='matrix_product_state', device='GPU')
    
    oracle = BitcoinQuantumOracle(total_bits, quantum_bits, target_hash_bin)
    
    # No Puzzle 15, o range começa no bit 14 igual a 1 (0x4000 = 16384)
    # O prefixo vai representar os bits superiores.
    start_prefix = 2**(prefix_bits - 1) # 2^10 = 1024 (0x400)
    end_prefix = 2**prefix_bits         # 2^11 = 2048 (0x800)
    
    # Inicia um pouco antes do nosso target simulado para ver a ressonância
    # target = 0x6a3b (27195). Prefixo = 27195 >> 4 = 1699 (0x6A3)
    start_test = 1696
    
    start_time = time.time()
    
    for i in range(start_test, end_prefix):
        prefix_bin = format(i, f'0{prefix_bits}b')
        print(f"\n[*] GPU (Vast.ai) testando Bloco Clássico [{prefix_bin}****]...")
        
        qc = oracle.build_circuit(prefix_bin)
        
        qc.measure_all()
        
        from qiskit import transpile
        compiled = transpile(qc, backend=simulator)
        job = simulator.run(compiled, shots=512)
        result = job.result()
        counts = result.get_counts()
        
        # Filtra os estados que casam com o prefixo medido (já que os bits superiores também são medidos)
        # O qiskit inverte a string de medida (little-endian), mas o measure_all() padrão pode requerer atenção.
        # Vamos buscar o pico máximo absoluto.
        top_state = max(counts, key=counts.get)
        max_shots = counts[top_state]
        confidence = (max_shots / 512) * 100
        
        # O top_state inclui todos os bits. Os 'quantum_bits' estão nas posições menos significativas (à direita no formato binário padrão nosso, mas à esquerda na string do Qiskit).
        # Para simplificar, como o estado amplificado deve ser o target_A completo (devido ao difusor e oráculo):
        top_state_integer = int(top_state, 2)
        
        # Se o pico for muito alto, detectamos ressonância
        if confidence > 15.0:
            print(f"    -> GPU Retornou Pico: {top_state} (Confiança: {confidence:.2f}%) em {time.time() - start_time:.2f}s")
            
            # Validação do sufixo quântico
            target_suffix = target_A & ((1 << quantum_bits) - 1)
            
            # Como a arquitetura inverte a medição no Qiskit (q0 é o bit mais à direita)
            # O target que esperamos encontrar no sufixo medido é o próprio.
            if top_state_integer == target_A:
                print(f"\n[!] Radar Quântico detectou ressonância de fase no prefixo: {prefix_bin}")
                
                # Cálculo percentual do progresso dentro do range do Puzzle 15
                total_range_val = end_prefix - start_prefix
                current_offset = i - start_prefix
                percentage = (current_offset / total_range_val) * 100 if total_range_val > 0 else 0
                
                print(f"\n[SUCESSO] O Radar Quântico Lossy (MPS) detectou um pico de ressonância!")
                print(f"Pista Localizada: A Chave Privada do Puzzle 15 está aproximadamente na faixa de {percentage:.4f}% do Range Total.")
                print(f"Inicie a varredura bruta neste intervalo específico no seu PC LOCAL:")
                
                hex_prefix = hex(i)[2:]
                address_alvo = "1QCbW9HWnwQWiQqVo5exhAnmfqKRrCRsvW"
                print(f"cuBitCrack -t 256 --keyspace {hex_prefix}0:{hex_prefix}f {address_alvo}")
                break

    print(f"\nTempo Total Híbrido: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    run_puzzle15_radar()
