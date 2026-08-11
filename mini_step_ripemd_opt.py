# mini_step_ripemd_opt.py
"""
Fase 6: Otimização de Hipergrafo via Tensor Slicing
Circuito original do Mini-Step de Compressão (22 Qubits).
Otimização profunda do backend cuTensorNet para evitar estouro de VRAM e acelerar a contração.
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
    for i in range(n):
        qc.rccx(reg_b[i], reg_c[i], reg_res[i])
        qc.x(reg_b[i])
        qc.rccx(reg_b[i], reg_d[i], reg_res[i])
        qc.x(reg_b[i])

def main():
    n = 3
    print("\n==========================================================")
    print("   FASE 6: OTIMIZAÇÃO POR TENSOR SLICING (cuTensorNet)")
    print("   Circuito: Step RIPEMD-160 | Qubits: 22")
    print("==========================================================")
    
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
    
    qc.x(reg_a[0])
    qc.x(reg_b[0])
    qc.x(reg_d[0])
    qc.x(reg_k[1]) 
    qc.barrier()
    
    ripemd_g_func_bitwise(qc, reg_b, reg_c, reg_d, reg_res, n)
    qc.barrier()
    
    cuccaro_inst = build_cuccaro_adder_instruction(n)
    
    qc.append(cuccaro_inst, [cin1[0]] + list(reg_a) + list(reg_res) + [cout1[0]])
    qc.barrier()
    
    qc.append(cuccaro_inst, [cin2[0]] + list(reg_k) + list(reg_res) + [cout2[0]])
    qc.barrier()
    
    qc.measure(reg_a, c_a)
    qc.measure(reg_b, c_b)
    qc.measure(reg_c, c_c)
    qc.measure(reg_d, c_d)
    print("\n[!] Ajustando hiperparâmetros de Slicing e Otimização Tensorial no cuTensorNet...")
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        # OTIMIZAÇÃO AVANÇADA DO CUTENSORNET:
        # Como o max_memory_mb=512 acionou um erro interno do otimizador de caminhos do grafo,
        # vamos usar opções suportadas mais específicas para fatiamento ou fallback de segurança.
        # Vamos passar as flags de blocking_enable que podem facilitar a divisão do tensor.
        simulator.set_options(
            blocking_enable=True,
            blocking_qubits=15
        )
        
        compiled = transpile(qc, simulator)
        
        print("Iniciando contração tensorial fatiada (Strict cuTensorNet)...")
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
        
    except Exception as e:
        print(f"\n[AVISO]: O tensor_network falhou internamente na otimização de fatiamento. Erro: {e}")
        print("Ativando Fallback Otimizado para Statevector na GPU...")
        simulator = AerSimulator(method='statevector', device='GPU')
        # Limita paralelismo de precisão mista que pode sobrecarregar a memória
        simulator.set_options(
            max_memory_mb=4000, 
            statevector_parallel_threshold=18
        )
        compiled = transpile(qc, simulator)
        
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
        
    counts = result.get_counts()
    
    print(f"Tempo de execução (GPU Otimizada): {t_end - t_start:.4f}s")
    for state, count in counts.items():
        parts = state.split(' ')
        val_res = parts[0]
        val_d = parts[1]
        val_c = parts[2]
        val_b = parts[3]
        val_a = parts[4]
        
        print("\n--- RESULTADO DA CASCATA OTIMIZADA ---")
        print(f"Resultado Final (Res) : Binário [{val_res}] -> Decimal: {int(val_res, 2)}")
        print(f"Verificação de Input  : A={val_a} | B={val_b} | C={val_c} | D={val_d}")
        if val_res == '011':
            print("[SUCESSO] Configuração suportada e fidelidade preservada!")

if __name__ == "__main__":
    main()
