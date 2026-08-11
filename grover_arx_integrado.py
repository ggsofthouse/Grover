# grover_arx_integrado.py
"""
FASE FINAL (PoC): Oráculo de Grover Integrado
Unificação do Mini-Step de compressão RIPEMD-160 dentro do motor de busca de Grover.
Alvo Hash: 3 (011). Constantes: B=1, C=0, D=1, K=2. Pré-imagem esperada em A: 1 (001).
"""

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
    """
    Função G(B,C,D) do RIPEMD-160
    """
    for i in range(n):
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])

def uncompute_ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n):
    """
    Reversão estrita da Função G
    """
    for i in range(n):
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])

def apply_diffuser(qc, search_reg):
    """ Difusor de Grover para reflexão sobre a média """
    n = len(search_reg)
    qc.h(search_reg)
    qc.x(search_reg)
    
    # MCZ (Multi-Controlled Z)
    qc.h(search_reg[-1])
    qc.mcx(search_reg[:-1], search_reg[-1])
    qc.h(search_reg[-1])
    
    qc.x(search_reg)
    qc.h(search_reg)

def main():
    n = 3
    print("\n==========================================================")
    print("   GROVER ARX INTEGRADO: PRE-IMAGE ATTACK END-TO-END")
    print("   Oráculo: Hash(A) = A + g(B,C,D) + K (mod 8)")
    print("   Hash Alvo: 3 (011) | Pré-imagem Esperada (A): 1 (001)")
    print("==========================================================")
    
    # 23 Qubits no total
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
    
    c_a = ClassicalRegister(n, 'meas_A')
    
    qc = QuantumCircuit(reg_a, reg_b, reg_c, reg_d, reg_k, reg_res, cin1, cout1, cin2, cout2, ancilla, c_a)
    
    # ---------------------------------------------------------
    # 1. INICIALIZAÇÃO
    # ---------------------------------------------------------
    # Busca em superposição total
    qc.h(reg_a)
    
    # Ancilla para Kickback (|->)
    qc.x(ancilla)
    qc.h(ancilla)
    
    # Constantes Hardcoded
    qc.x(reg_b[0]) # B = 1
    # C = 0
    qc.x(reg_d[0]) # D = 1
    qc.x(reg_k[1]) # K = 2 (010)
    
    qc.barrier()
    
    cuccaro_inst = build_cuccaro_adder_instruction(n)
    cuccaro_sub = cuccaro_inst.inverse()
    
    iterations = math.floor((math.pi / 4) * math.sqrt(2 ** n))
    print(f"Número de iterações de Grover calculadas: {iterations}")
    
    for _ in range(iterations):
        # ==========================================
        # ORÁCULO U_f (Mini-Step RIPEMD)
        # ==========================================
        # a) g(B,C,D) -> Res
        ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
        
        # b) Res + A -> Res
        qc.append(cuccaro_inst, [cin1[0]] + list(reg_a) + list(reg_res) + [cout1[0]])
        
        # c) Res + K -> Res
        qc.append(cuccaro_inst, [cin2[0]] + list(reg_k) + list(reg_res) + [cout2[0]])
        
        # ==========================================
        # PHASE KICKBACK (Comparação com Hash Alvo = 011)
        # ==========================================
        # LSB=1, Bit1=1, MSB=0. Invertemos o MSB para ativar o MCX.
        qc.x(reg_res[2])
        qc.mcx(reg_res, ancilla[0])
        qc.x(reg_res[2]) # Desfaz
        
        # ==========================================
        # UNCOMPUTE TOTAL DO ORÁCULO (Reversão)
        # ==========================================
        # Inverte (c): Res - K
        qc.append(cuccaro_sub, [cin2[0]] + list(reg_k) + list(reg_res) + [cout2[0]])
        
        # Inverte (b): Res - A
        qc.append(cuccaro_sub, [cin1[0]] + list(reg_a) + list(reg_res) + [cout1[0]])
        
        # Inverte (a): Desfaz g(B,C,D)
        uncompute_ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
        
        qc.barrier()
        
        # ==========================================
        # DIFUSOR
        # ==========================================
        apply_diffuser(qc, reg_a)
        qc.barrier()
        
    # Medimos apenas o registrador A (o espaço de busca)
    qc.measure(reg_a, c_a)
    
    print("\n[!] Circuito Unificado construído (23 Qubits, Múltiplos Steps). Iniciando simulador...")
    
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        # Otimizações de Tensor Slicing provadas na Fase 6
        simulator.set_options(
            blocking_enable=True,
            blocking_qubits=15
        )
        
        compiled = transpile(qc, simulator)
        
        print("Iniciando contração tensorial de rede profunda (Strict cuTensorNet)...")
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        counts = result.get_counts()
        t_end = time.time()
        
    except Exception as e:
        print(f"\n[AVISO]: O tensor_network falhou (Profundidade Extrema do Grover). Erro: {e}")
        print("Ativando Fallback Otimizado para Statevector na GPU (VRAM de 23 Qubits ~ 128MB)...")
        simulator = AerSimulator(method='statevector', device='GPU')
        simulator.set_options(
            max_memory_mb=4000, 
            statevector_parallel_threshold=18
        )
        compiled = transpile(qc, simulator)
        
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        counts = result.get_counts()
        t_end = time.time()
        
    print(f"Tempo de execução (GPU): {t_end - t_start:.4f}s")
    
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state, top_shots = sorted_counts[0]
    top_decimal = int(top_state, 2)
    
    print("\n--- RESULTADO DA BUSCA DE PRE-IMAGE ---")
    print(f"Chave Encontrada (A) : Binário [{top_state}] -> Decimal: {top_decimal}")
    print(f"Confiança (Shots)    : {(top_shots/1024)*100:.2f}% dos colapsos")
    
    if top_decimal == 1:
        print("\n[HACK SUCESSO] Grover cruzou o Oráculo Completo do RIPEMD e achou a pré-imagem 001!")
    else:
        print("\n[FALHA] Colapso incorreto. Verifique o Uncompute ou o Diffuser.")

if __name__ == "__main__":
    main()
