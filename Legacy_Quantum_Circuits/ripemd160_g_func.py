# ripemd160_g_func.py
"""
Fase 4: Modelagem Estrutural do RIPEMD-160
Implementação da função booleana não-linear do Round 2:
g(x, y, z) = (x AND y) XOR (NOT x AND z)
"""

import time
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

def ripemd_g_func(qc, x, y, z, res):
    """
    Constrói o bloco RIPEMD_G_FUNC: g(x,y,z) = (x & y) ^ (~x & z)
    Utiliza a Ancilla 'res' (inicializada em 0) para acumular o resultado via XOR.
    Os registradores originais x, y, z são rigorosamente preservados.
    """
    # 1. Acumula (x AND y) na Ancilla
    qc.rccx(x, y, res)
    
    # 2. Inverte x temporariamente para computar ~x
    qc.x(x)
    
    # 3. Acumula (~x AND z) na Ancilla via XOR
    # A operação XOR é válida matematicamente pois (x & y) e (~x & z) são mutuamente exclusivos.
    qc.rccx(x, z, res)
    
    # 4. Restaura x ao seu estado original (Uncompute local)
    qc.x(x)

def build_test_circuit(input_state):
    """
    Constrói o circuito de teste para o estado 'input_state' (tupla de x, y, z)
    """
    q_x = QuantumRegister(1, 'x')
    q_y = QuantumRegister(1, 'y')
    q_z = QuantumRegister(1, 'z')
    q_res = QuantumRegister(1, 'res')
    
    # Registradores clássicos para verificação (ordem: res, zyx)
    c_inputs = ClassicalRegister(3, 'meas_inputs_zyx')
    c_res = ClassicalRegister(1, 'meas_res')
    
    qc = QuantumCircuit(q_x, q_y, q_z, q_res, c_inputs, c_res)
    
    # ----------------------------------------------------
    # INICIALIZAÇÃO HARDCODED
    # ----------------------------------------------------
    val_x, val_y, val_z = input_state
    if val_x == 1: qc.x(q_x)
    if val_y == 1: qc.x(q_y)
    if val_z == 1: qc.x(q_z)
    
    qc.barrier()
    
    # ----------------------------------------------------
    # BLOCO FUNCIONAL NÃO-LINEAR
    # ----------------------------------------------------
    ripemd_g_func(qc, q_x, q_y, q_z, q_res)
    
    qc.barrier()
    
    # ----------------------------------------------------
    # MEDIÇÃO (Validação do Uncompute)
    # ----------------------------------------------------
    qc.measure([q_x[0], q_y[0], q_z[0]], c_inputs)
    qc.measure(q_res[0], c_res)
    
    return qc

def run_test(input_state):
    print(f"\n--- TESTANDO INPUT (x={input_state[0]}, y={input_state[1]}, z={input_state[2]}) ---")
    qc = build_test_circuit(input_state)
    
    if input_state == (1, 0, 1):
        print("\n[!] Arquitetura de Portas do Bloco RIPEMD_G_FUNC:")
        print(qc.draw(fold=-1))
    
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
    except Exception as e:
        print("[AVISO] Fallback interno para cuStateVec...")
        simulator = AerSimulator(method='statevector', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
        
    counts = result.get_counts()
    
    print(f"Tempo de execução (GPU): {t_end - t_start:.4f}s")
    for state, count in counts.items():
        # A medição é retornada formatada como "meas_res meas_inputs_zyx"
        parts = state.split(' ')
        val_res = parts[0]
        val_inputs = parts[1]
        
        orig_zyx = f"{input_state[2]}{input_state[1]}{input_state[0]}"
        
        print(f"Inputs Restaurados (z,y,x): Binário [{val_inputs}] | Original Esperado: [{orig_zyx}]")
        print(f"Resultado Ancilla g(x,y,z): {val_res}")
        
        if val_inputs == orig_zyx:
            print("Status de Preservação (Uncompute): [SUCESSO]")
        else:
            print("Status de Preservação (Uncompute): [FALHA]")

def main():
    print("\n==========================================================")
    print("   MODELAGEM ESTRUTURAL RIPEMD-160: Função G (Round 2)")
    print("   g(x, y, z) = (x AND y) XOR (NOT x AND z)")
    print("==========================================================")
    
    # Teste 1: x=1, y=0, z=1 -> g = (1&0) ^ (0&1) = 0
    run_test((1, 0, 1))
    
    # Teste 2: x=0, y=1, z=1 -> g = (0&1) ^ (1&1) = 1
    run_test((0, 1, 1))

if __name__ == "__main__":
    main()
