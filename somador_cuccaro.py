# somador_cuccaro.py
"""
Fase 2: Aritmética Quântica - Somador de Cuccaro (Ripple-Carry Adder)
Implementação explícita de Adição Modular Reversível para arquitetura ARX (RIPEMD-160).
Execução acelerada via cuTensorNet na GPU.
"""

import time
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

def maj(qc, c, a, b):
    """
    Bloco MAJ (Majority):
    Calcula o carry-out e propaga o bit. O carry-out é armazenado no qubit 'a'.
    """
    qc.cx(a, b)
    qc.cx(a, c)
    qc.rccx(b, c, a)

def uma(qc, c, a, b):
    """
    Bloco UMA (UnMajority and Add):
    Desfaz o MAJ (Uncompute interno) para restaurar os registradores A e C originais,
    e calcula a soma, armazenando-a diretamente no registrador B.
    """
    qc.rccx(b, c, a)
    qc.cx(a, c)
    qc.cx(c, b)

def build_cuccaro_adder(n):
    # Definindo os registradores Quânticos
    cin = QuantumRegister(1, 'c_in')
    a = QuantumRegister(n, 'a')
    b = QuantumRegister(n, 'b')
    cout = QuantumRegister(1, 'c_out')
    
    # Registradores clássicos para medir o resultado final
    cb = ClassicalRegister(n, 'meas_b')
    ca = ClassicalRegister(n, 'meas_a')
    
    qc = QuantumCircuit(cin, a, b, cout, cb, ca)
    
    # ----------------------------------------------------
    # 1. PREPARAÇÃO DOS ESTADOS (Hardcode)
    # ----------------------------------------------------
    # A = 3 (Binário: 011 -> LSB=1, MSB=0)
    qc.x(a[0])
    qc.x(a[1])
    
    # B = 2 (Binário: 010 -> LSB=0, Bit1=1, MSB=0)
    qc.x(b[1])
    
    qc.barrier()
    
    # ----------------------------------------------------
    # 2. PROPAGAÇÃO DO CARRY (Fase MAJ)
    # ----------------------------------------------------
    maj(qc, cin[0], a[0], b[0])
    for i in range(1, n):
        maj(qc, a[i-1], a[i], b[i])
        
    # Copia o Carry-Out Final
    qc.cx(a[n-1], cout[0])
    
    # ----------------------------------------------------
    # 3. SOMA E UNCOMPUTE (Fase UMA)
    # ----------------------------------------------------
    for i in reversed(range(1, n)):
        uma(qc, a[i-1], a[i], b[i])
    uma(qc, cin[0], a[0], b[0])
    
    qc.barrier()
    
    # 4. MEDIÇÃO
    qc.measure(b, cb)
    qc.measure(a, ca)
    
    return qc
    
def main():
    n_bits = 3
    qc = build_cuccaro_adder(n_bits)
    
    print("\n==========================================================")
    print("   ARITMÉTICA QUÂNTICA: Somador de Cuccaro (Ripple-Carry)")
    print("   Alvo: A = 3, B = 2  =>  Resultado Esperado: B = 5")
    print("==========================================================")
    
    print("\n[!] Desenho da Arquitetura de Portas (MAJ e UMA explicitados):")
    print(qc.draw(fold=-1))
    
    print("\nInicializando simulador AerSimulator (GPU / Tensor Network)...")
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
    except Exception as e:
        print(f"Erro ao instanciar GPU: {e}")
        return
    
    try:
        t_start = time.time()
        compiled = transpile(qc, simulator)
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
    except Exception as e:
        print(f"\n[AVISO] Erro interno do cuTensorNet no WSL detectado (CUTENSORNET_STATUS_INTERNAL_ERROR).")
        print("Realizando fallback automático para simulação statevector acelerada na GPU (cuStateVec)...")
        simulator = AerSimulator(method='statevector', device='GPU')
        t_start = time.time()
        compiled = transpile(qc, simulator)
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
    
    counts = result.get_counts()
    
    print(f"Status do job: {result.status}")
    print(f"Tempo de execução (Contração Tensorial GPU): {t_end - t_start:.4f}s")
    
    print("\n--- RESULTADO DA SOMA QUÂNTICA (1024 Shots) ---")
    for state, count in counts.items():
        # state vem no formato "ca cb" devido à ordem de registro no circuito
        parts = state.split(' ')
        if len(parts) == 2:
            val_a, val_b = parts[0], parts[1]
        else:
            val_a, val_b = "ERROR", "ERROR"
            
        int_a = int(val_a, 2)
        int_b = int(val_b, 2)
        
        print(f"Probabilidade: {(count/1024)*100:.2f}% dos colapsos")
        print(f"Registrador A (Restaurado): Binário [{val_a}] -> Decimal: {int_a}")
        print(f"Registrador B (Soma A+B)  : Binário [{val_b}] -> Decimal: {int_b}")
        
        if int_b == 5 and int_a == 3:
            print("\n[SUCESSO] Adição Modular reversível perfeitamente uncomputed e executada na GPU!")
        else:
            print("\n[FALHA] O resultado não confere com o esperado (A=3, B=5).")

if __name__ == "__main__":
    main()
