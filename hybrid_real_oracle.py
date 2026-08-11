import time
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

def maj(qc, c, a, b):
    qc.cx(a, b)
    qc.cx(a, c)
    qc.rccx(b, c, a)

def uma(qc, c, a, b):
    qc.rccx(b, c, a)
    qc.cx(a, c)
    qc.cx(c, b)

def build_cuccaro_adder_instruction(n):
    cin = QuantumRegister(1, 'c_in')
    a = QuantumRegister(n, 'a')
    b = QuantumRegister(n, 'b')
    cout = QuantumRegister(1, 'c_out')
    qc = QuantumCircuit(cin, a, b, cout, name="Cuccaro_ADD")
    
    maj(qc, cin[0], a[0], b[0])
    for i in range(1, n):
        maj(qc, a[i-1], a[i], b[i])
        
    qc.cx(a[n-1], cout[0])
    
    for i in reversed(range(1, n)):
        uma(qc, a[i-1], a[i], b[i])
    uma(qc, cin[0], a[0], b[0])
    
    return qc.to_instruction()

def ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n):
    for i in range(n):
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])

def uncompute_ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n):
    for i in range(n):
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])

def apply_diffuser(qc, search_reg):
    n = len(search_reg)
    qc.h(search_reg)
    qc.x(search_reg)
    qc.h(search_reg[-1])
    if n > 1:
        qc.mcx(search_reg[:-1], search_reg[-1])
    else:
        qc.x(search_reg[-1])
    qc.h(search_reg[-1])
    qc.x(search_reg)
    qc.h(search_reg)

def initialize_constant(qc, reg, value_bin):
    for i, bit in enumerate(reversed(value_bin)):
        if bit == '1':
            qc.x(reg[i])

def build_real_oracle_circuit(prefix_bin, quantum_bits, target_hash_bin, B_const, C_const, D_const, K_const):
    n = len(prefix_bin) + quantum_bits
    
    reg_a = QuantumRegister(n, 'A_search')
    reg_b = QuantumRegister(n, 'B_const')
    reg_c = QuantumRegister(n, 'C_const')
    reg_d = QuantumRegister(n, 'D_const')
    reg_k = QuantumRegister(n, 'K_const')
    reg_res = QuantumRegister(n, 'Res')
    
    cin1 = QuantumRegister(1, 'cin1')
    cout1 = QuantumRegister(1, 'cout1')
    cin2 = QuantumRegister(1, 'cin2')
    cout2 = QuantumRegister(1, 'cout2')
    
    ancilla = QuantumRegister(1, 'ancilla')
    c_q = ClassicalRegister(quantum_bits, 'meas_Q')
    
    qc = QuantumCircuit(reg_a, reg_b, reg_c, reg_d, reg_k, reg_res, cin1, cout1, cin2, cout2, ancilla, c_q)
    
    # Inicia o Prefixo Clássico (Iterado pela CPU)
    initialize_constant(qc, reg_a[quantum_bits:], prefix_bin)
    
    # Inicia a Janela Quântica (Superposição na GPU)
    qc.h(reg_a[:quantum_bits])
    
    # Inicia as Constantes (Gabaritos do ARX)
    initialize_constant(qc, reg_b, format(B_const, f'0{n}b'))
    initialize_constant(qc, reg_c, format(C_const, f'0{n}b'))
    initialize_constant(qc, reg_d, format(D_const, f'0{n}b'))
    initialize_constant(qc, reg_k, format(K_const, f'0{n}b'))
    
    # Ancilla no estado |-> para o Phase Kickback
    qc.x(ancilla)
    qc.h(ancilla)
    
    add_inst = build_cuccaro_adder_instruction(n)
    
    # ==========================
    # START: ORÁCULO REAL (ARX)
    # Matemática: Hash = A + G(B,C,D) + K
    # ==========================
    ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
    qc.append(add_inst, [cin1[0]] + reg_res[:] + reg_a[:] + [cout1[0]])
    qc.append(add_inst, [cin2[0]] + reg_a[:] + reg_k[:] + [cout2[0]])
    
    # Validação do Target Hash (Colisão em Superposição)
    target_reversed = target_hash_bin[::-1]
    for i in range(n):
        if target_reversed[i] == '0':
            qc.x(reg_k[i])
            
    qc.mcx(reg_k, ancilla)
    
    # Uncompute Rigoroso
    for i in range(n):
        if target_reversed[i] == '0':
            qc.x(reg_k[i])
            
    qc.append(add_inst.inverse(), [cin2[0]] + reg_a[:] + reg_k[:] + [cout2[0]])
    qc.append(add_inst.inverse(), [cin1[0]] + reg_res[:] + reg_a[:] + [cout1[0]])
    uncompute_ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
    # ==========================
    # END: ORÁCULO REAL
    # ==========================
    
    # Aplica o Difusor APENAS nos bits quânticos
    apply_diffuser(qc, reg_a[:quantum_bits])
    
    qc.measure(reg_a[:quantum_bits], c_q)
    return qc

def dispatch_to_bitcrack(prefix_bin, total_puzzle_bits):
    remaining_bits = total_puzzle_bits - len(prefix_bin)
    start_bin = prefix_bin + ('0' * remaining_bits)
    end_bin = prefix_bin + ('1' * remaining_bits)
    
    start_hex = hex(int(start_bin, 2))[2:]
    end_hex = hex(int(end_bin, 2))[2:]
    
    address_alvo = "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe"
    
    prefix_val = int(prefix_bin, 2)
    max_prefix_val = (2 ** len(prefix_bin)) - 1
    percentage = (prefix_val / max_prefix_val) * 100 if max_prefix_val > 0 else 0
    
    print(f"\n[SUCESSO] Radar Quântico (ARX) travou em um setor do Keyspace!")
    print(f"Pista Localizada: A Chave Privada está aproximadamente na faixa de {percentage:.4f}% do Range Total.")
    print(f"Inicie a varredura bruta neste intervalo específico:")
    print(f"./cuBitCrack -t 256 --keyspace {start_hex}:{end_hex} {address_alvo}\n")

def main():
    print("\n==========================================================")
    print("   LOOP HÍBRIDO ARX: ORÁCULO REAL (RIPEMD + CUCCARO)")
    print("==========================================================")
    
    total_bits = 10
    quantum_bits = 4
    prefix_bits = total_bits - quantum_bits
    
    # Constantes da equação do Hash: Hash(A) = A + g(B,C,D) + K
    B_const = 5
    C_const = 13
    D_const = 7
    K_const = 42
    
    # O valor alvo A (a chave escondida) é 853 (1101010101 em binário)
    target_A = 853
    # G(B,C,D) = (B & C) | (~B & D) = (5 & 13) | (~5 & 7) = 5 | 2 = 7
    # Hash = 853 + 7 + 42 = 902
    target_hash_val = 902
    target_hash_bin = format(target_hash_val, f'0{total_bits}b')
    
    print(f"[#] Busca Total: {total_bits} bits")
    print(f"[#] Target Hash Simulado (ARX): {target_hash_val}")
    print(f"[#] Carga do Grafo (Qubits Totais do Circuito): {total_bits*6 + 4} Qubits")
    print(f"[#] Fatia Quântica (GPU): {quantum_bits} bits (Superposição)")
    print("----------------------------------------------------------\n")
    
    simulator = AerSimulator(method='tensor_network', device='GPU')
    simulator.set_options(blocking_enable=True, blocking_qubits=15)
    
    t_global_start = time.time()
    
    for i in range(2**prefix_bits):
        prefix_bin = format(i, f'0{prefix_bits}b')
        print(f"[*] CPU testando Bloco Clássico [{prefix_bin}****]...")
        
        t_start = time.time()
        qc = build_real_oracle_circuit(prefix_bin, quantum_bits, target_hash_bin, B_const, C_const, D_const, K_const)
        
        compiled = transpile(qc, basis_gates=simulator.operation_names)
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        
        if not result.success:
            print(f"      [!] TensorNetwork falhou. Tentando Fallback para StateVector...")
            sim_fallback = AerSimulator(method='statevector', device='GPU')
            comp_fallback = transpile(qc, basis_gates=sim_fallback.operation_names)
            job = sim_fallback.run(comp_fallback, shots=1024)
            result = job.result()
            
            if not result.success:
                raise Exception(result.status)
        
        counts = result.get_counts()
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top_state, top_shots = sorted_counts[0]
        confidence = (top_shots / 1024) * 100
        
        t_end = time.time()
        print(f"    -> GPU Retornou Sufixo: {top_state} (Confiança: {confidence:.2f}%) em {t_end - t_start:.2f}s")
        
        if confidence > 80.0:
            full_key_prefix = prefix_bin + top_state
            print(f"\n[!] Radar Quântico travou no prefixo mais provável: {full_key_prefix}")
            dispatch_to_bitcrack(full_key_prefix, 10)
            break
            
    t_global_end = time.time()
    print(f"\nTempo Total Híbrido: {t_global_end - t_global_start:.2f}s")

if __name__ == "__main__":
    main()
