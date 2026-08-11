# mini_step_ripemd.py
"""
Fase 5: O Step de Compressão Miniaturizado (RIPEMD-160)
Integração estrutural: Adição Modular (Fase 2) + Bloco Não-Linear G (Fase 4).
Equação: Result = A + g(B,C,D) + K (mod 8)
"""

import time
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
    Aplica a função G do RIPEMD-160 bit a bit ao longo da palavra.
    """
    for i in range(n):
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])

def main():
    n = 3
    print("\n==========================================================")
    print("   FASE 5: O STEP DE COMPRESSÃO MINIATURIZADO (RIPEMD-160)")
    print("   Equação: Res = A + g(B,C,D) + K (mod 8)")
    print("==========================================================")
    
    # 22 Qubits no total
    reg_a = QuantumRegister(n, 'A')
    reg_b = QuantumRegister(n, 'B')
    reg_c = QuantumRegister(n, 'C')
    reg_d = QuantumRegister(n, 'D')
    reg_k = QuantumRegister(n, 'K')
    reg_res = QuantumRegister(n, 'Res')
    
    cin1 = QuantumRegister(1, 'cin1')
    cout1 = QuantumRegister(1, 'cout1')
    cin2 = QuantumRegister(1, 'cin2')
    cout2 = QuantumRegister(1, 'cout2')
    
    c_a = ClassicalRegister(n, 'meas_A')
    c_b = ClassicalRegister(n, 'meas_B')
    c_c = ClassicalRegister(n, 'meas_C')
    c_d = ClassicalRegister(n, 'meas_D')
    c_res = ClassicalRegister(n, 'meas_Res')
    
    qc = QuantumCircuit(reg_a, reg_b, reg_c, reg_d, reg_k, reg_res, cin1, cout1, cin2, cout2, c_a, c_b, c_c, c_d, c_res)
    
    # ---------------------------------------------------------
    # 1. INICIALIZAÇÃO HARDCODED (Para teste de colapso)
    # ---------------------------------------------------------
    qc.x(reg_a[0]) # A = 1 (001)
    qc.x(reg_b[0]) # B = 1 (001)
    # C = 0 (000)
    qc.x(reg_d[0]) # D = 1 (001)
    
    # Injeção de Constante K = 2 (010)
    qc.x(reg_k[1]) 
    
    qc.barrier()
    
    # ---------------------------------------------------------
    # 2. CASCATA COMPUTACIONAL DO ROUND
    # ---------------------------------------------------------
    
    # a) Avalia g(B,C,D) diretamente no registrador Res
    ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
    qc.barrier()
    
    cuccaro_inst = build_cuccaro_adder_instruction(n)
    
    # b) Soma A no Res: Res = Res(g) + A
    qc.append(cuccaro_inst, [cin1[0]] + list(reg_a) + list(reg_res) + [cout1[0]])
    qc.barrier()
    
    # c) Soma K no Res: Res = Res(g+A) + K
    qc.append(cuccaro_inst, [cin2[0]] + list(reg_k) + list(reg_res) + [cout2[0]])
    qc.barrier()
    
    # ---------------------------------------------------------
    # 3. MEDIÇÕES
    # ---------------------------------------------------------
    qc.measure(reg_a, c_a)
    qc.measure(reg_b, c_b)
    qc.measure(reg_c, c_c)
    qc.measure(reg_d, c_d)
    qc.measure(reg_res, c_res)
    
    print("\n[!] Circuito Funcional do Step construído (22 Qubits). Iniciando contração tensorial...")
    
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
    except Exception as e:
        print("[AVISO] Fallback interno para cuStateVec devido à topologia densa no WSL...")
        simulator = AerSimulator(method='statevector', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
        
    counts = result.get_counts()
    
    print(f"Tempo de execução (GPU): {t_end - t_start:.4f}s")
    for state, count in counts.items():
        # A ordem das medições (pela adição no QuantumCircuit) é: c_res, c_d, c_c, c_b, c_a
        parts = state.split(' ')
        val_res = parts[0]
        val_d = parts[1]
        val_c = parts[2]
        val_b = parts[3]
        val_a = parts[4]
        
        print("\n--- RESULTADO DA CASCATA QUÂNTICA ---")
        print(f"Probabilidade do colapso: {(count/1024)*100:.2f}%")
        print(f"Resultado Final (Res) : Binário [{val_res}] -> Decimal: {int(val_res, 2)}")
        print(f"Registrador A (Intacto) : Binário [{val_a}] (Esperado: 001)")
        print(f"Registrador B (Intacto) : Binário [{val_b}] (Esperado: 001)")
        print(f"Registrador C (Intacto) : Binário [{val_c}] (Esperado: 000)")
        print(f"Registrador D (Intacto) : Binário [{val_d}] (Esperado: 001)")
        
        if val_res == '011' and val_a == '001' and val_b == '001' and val_c == '000' and val_d == '001':
            print("\n[SUCESSO] Mini-Step de compressão executado perfeitamente! Os registradores de entrada não foram poluídos.")
        else:
            print("\n[FALHA] Colapso incorreto. O uncompute falhou em algum bloco.")

if __name__ == "__main__":
    main()
