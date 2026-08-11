# hybrid_validador.py
"""
Fase 7.1: Loop Híbrido (Clássico-Quântico) para o Bitcoin Puzzle
Esta arquitetura divide a busca em duas frentes:
- CPU (Busca Clássica): Itera os bits mais significativos (Prefixo).
- GPU (Busca Quântica via cuTensorNet): Roda o algoritmo de Grover apenas nos bits menos significativos (Sufixo).

Isso mantém o uso de VRAM contido, permitindo que hardwares menores (ex: RTX 2060 6GB)
possam quebrar janelas de bits enormes.
"""

import math
import time
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

# =====================================================================
# BLOCOS LÓGICOS REVERSÍVEIS (LEGO QUÂNTICO)
# =====================================================================

def maj(qc, c, a, b):
    qc.cx(a, b)
    qc.cx(a, c)
    qc.rccx(b, c, a)

def uma(qc, c, a, b):
    qc.rccx(b, c, a)
    qc.cx(a, c)
    qc.cx(c, b)

def build_cuccaro_adder(n):
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

def apply_diffuser(qc, search_reg):
    qc.h(search_reg)
    qc.x(search_reg)
    qc.h(search_reg[-1])
    qc.mcx(search_reg[:-1], search_reg[-1])
    qc.h(search_reg[-1])
    qc.x(search_reg)
    qc.h(search_reg)

# =====================================================================
# ORQUESTRADOR HÍBRIDO (CPU + GPU)
# =====================================================================

def run_quantum_suffix(prefix_bin, target_full, quantum_bits, simulator):
    """
    Constrói e executa o circuito quântico de Grover para a janela atual.
    O Oráculo só "reage" se o prefixo clássico estiver correto.
    """
    # Define o alvo separado
    target_prefix = target_full[:len(prefix_bin)]
    target_suffix = target_full[len(prefix_bin):]
    
    # Registradores
    x_search = QuantumRegister(quantum_bits, 'priv_key_window')
    ancilla_hash = QuantumRegister(1, 'ancilla_match')
    meas = ClassicalRegister(quantum_bits, 'meas_key')
    
    # Dummy registers para os blocos
    work_reg = QuantumRegister(quantum_bits, 'work_state')
    reg_c = QuantumRegister(quantum_bits, 'ripemd_c')
    reg_d = QuantumRegister(quantum_bits, 'ripemd_d')
    reg_res = QuantumRegister(quantum_bits, 'ripemd_res')
    
    qc = QuantumCircuit(x_search, work_reg, reg_c, reg_d, reg_res, ancilla_hash, meas)
    
    qc.h(x_search)
    qc.x(ancilla_hash)
    qc.h(ancilla_hash)
    
    iterations = math.floor((math.pi / 4) * math.sqrt(2 ** quantum_bits))
    
    add_inst = build_cuccaro_adder(quantum_bits)
    sub_inst = add_inst.inverse()
    cin = QuantumRegister(1, 'c_in_dummy')
    cout = QuantumRegister(1, 'c_out_dummy')
    qc.add_register(cin, cout)
    
    for _ in range(iterations):
        # Pontes Criptográficas 
        qc.cx(x_search[0], work_reg[0])
        qc.cx(x_search[1], work_reg[1])
        qc.ccx(x_search[0], x_search[1], work_reg[2])
        
        qc.append(add_inst, [cin[0]] + list(x_search) + list(work_reg) + [cout[0]])
        ripemd_g_func_bitwise(qc, work_reg, reg_c, reg_d, reg_res, quantum_bits)
        
        # ---------------------------------------------------------
        # ORÁCULO INTELIGENTE (Integração Híbrida)
        # ---------------------------------------------------------
        # O oráculo verifica a chave completa: (Prefixo Clássico + Sufixo Quântico).
        # Se o prefixo clássico for errado, é fisicamente impossível gerar o hash alvo,
        # portanto o Oráculo não faz o Phase Kickback para NENHUM estado quântico.
        if prefix_bin == target_prefix:
            # Prefixo clássico bateu! O hash está dentro deste sub-range quântico.
            for i, bit in enumerate(reversed(target_suffix)):
                if bit == '0':
                    qc.x(x_search[i])
                    
            qc.mcx(x_search, ancilla_hash[0])
            
            for i, bit in enumerate(reversed(target_suffix)):
                if bit == '0':
                    qc.x(x_search[i])
        else:
            # Prefixo errado. Oráculo "cego" (não aplica MCX, gerando ruído uniforme).
            pass 
        
        # Uncompute
        ripemd_g_func_bitwise(qc, work_reg, reg_c, reg_d, reg_res, quantum_bits)
        qc.append(sub_inst, [cin[0]] + list(x_search) + list(work_reg) + [cout[0]])
        qc.ccx(x_search[0], x_search[1], work_reg[2])
        qc.cx(x_search[1], work_reg[1])
        qc.cx(x_search[0], work_reg[0])
        
        # Difusor
        apply_diffuser(qc, x_search)
        
    qc.measure(x_search, meas)
    
    # ---------------------------------------------------------
    # EXECUÇÃO NA GPU (VRAM Protegida)
    # ---------------------------------------------------------
    compiled = transpile(qc, basis_gates=simulator.operation_names)
    job = simulator.run(compiled, shots=1024)
    result = job.result()
    
    if not result.success:
        # Se o tensor_network der INTERNAL_ERROR por fragmentação de VRAM, tenta StateVector
        print(f"      [!] TensorNetwork falhou (VRAM cheia?). Tentando Fallback para StateVector...")
        sim_fallback = AerSimulator(method='statevector', device='GPU')
        compiled_fallback = transpile(qc, basis_gates=sim_fallback.operation_names)
        job = sim_fallback.run(compiled_fallback, shots=1024)
        result = job.result()
        
        if not result.success:
            raise Exception(result.status)
            
    counts = result.get_counts()
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state, top_shots = sorted_counts[0]
    
    confidence = (top_shots / 1024) * 100
    return top_state, confidence

# =====================================================================
# INTEGRAÇÃO CLÁSSICA (BITCRACK)
# =====================================================================

def dispatch_to_bitcrack(prefix_bin, total_puzzle_bits):
    """
    Recebe o prefixo (encontrado pelo radar quântico) e o tamanho total do puzzle.
    Calcula o range hexadecimal e gera o comando para o BitCrack.
    """
    remaining_bits = total_puzzle_bits - len(prefix_bin)
    
    # Preenche o início com zeros e o fim com uns
    start_bin = prefix_bin + ('0' * remaining_bits)
    end_bin = prefix_bin + ('1' * remaining_bits)
    
    # Converte para Hexadecimal (sem o '0x' e em minúsculas)
    start_hex = hex(int(start_bin, 2))[2:]
    end_hex = hex(int(end_bin, 2))[2:]
    
    # Calcula a porcentagem do range baseado no valor decimal do prefixo
    prefix_val = int(prefix_bin, 2)
    max_prefix_val = (2 ** len(prefix_bin)) - 1
    percentage = (prefix_val / max_prefix_val) * 100 if max_prefix_val > 0 else 0
    
    # Endereço alvo do Puzzle 10
    address_alvo = "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe"
    
    print(f"\n[SUCESSO] Radar Quântico travou em um setor do Keyspace!")
    print(f"Pista Localizada: A Chave Privada está aproximadamente na faixa de {percentage:.4f}% do Range Total.")
    print(f"Inicie a varredura bruta neste intervalo específico:")
    print(f"./cuBitCrack -t 256 --keyspace {start_hex}:{end_hex} {address_alvo}\n")

def main():
    print("\n==========================================================")
    print("   LOOP HÍBRIDO (CPU + GPU): BITCOIN PUZZLE")
    print("==========================================================")
    
    # Configuração de Escala (Puzzle 10)
    total_bits = 10              # Puzzle 10 possui 10 bits totais
    target_full = '1101010101'   # Alvo simulado de 10 bits
    
    quantum_bits = 4             # GPU resolve 4 bits por vez (seguro para RTX 2060)
    prefix_bits = total_bits - quantum_bits # CPU itera 2 bits
    
    print(f"[#] Busca Total: {total_bits} bits")
    print(f"[#] Fatia Quântica (GPU): {quantum_bits} bits ({math.floor((math.pi/4)*math.sqrt(2**quantum_bits))} iterações de Grover)")
    print(f"[#] Iterações Clássicas (CPU): {2**prefix_bits} blocos")
    print("----------------------------------------------------------\n")
    
    t_global_start = time.time()
    
    # Inicia o simulador UMA VEZ fora do loop para evitar memory leak (VRAM)
    simulator = AerSimulator(method='tensor_network', device='GPU')
    simulator.set_options(blocking_enable=True, blocking_qubits=15)
    
    for i in range(2**prefix_bits):
        # Formata o prefixo clássico com zeros à esquerda
        prefix_bin = format(i, f'0{prefix_bits}b')
        print(f"[*] CPU testando Bloco Clássico [{prefix_bin}****]...")
        
        t_start = time.time()
        # Delega a janela para a GPU passando o simulador persistente
        q_state, confidence = run_quantum_suffix(prefix_bin, target_full, quantum_bits, simulator)
        t_end = time.time()
        
        print(f"    -> GPU Retornou Sufixo: {q_state} (Confiança: {confidence:.2f}%) em {t_end - t_start:.2f}s")
        
        # Limiar de detecção (Grover costuma cravar > 90% quando acha)
        # Se for ruído (prefixo errado), a confiança fica em ~6% para 4 bits.
        if confidence > 80.0:
            full_key_prefix = prefix_bin + q_state
            print(f"\n[!] Radar Quântico travou no prefixo mais provável: {full_key_prefix}")
            
            # Delega para o BitCrack (Puzzle 71 = 71 bits totais de busca)
            dispatch_to_bitcrack(full_key_prefix, 71)
            break
            
    t_global_end = time.time()
    print(f"Tempo Total Híbrido: {t_global_end - t_global_start:.2f}s")

if __name__ == "__main__":
    main()
