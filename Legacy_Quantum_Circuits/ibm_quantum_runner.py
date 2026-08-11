# ibm_quantum_runner.py
"""
Ponte Física: Envio do Circuito Grover ARX para Computador Quântico Real (IBM Quantum).
Aviso: Circuitos profundos (centenas de portas lógicas) em hardware NISQ atual
resultam em Decoerência, o que significa que o resultado retornará fortemente ruído (ruído branco).
"""

import math
import os
import getpass
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_ibm_runtime.options import SamplerOptions

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
# CONEXÃO IBM E ENVIO
# =====================================================================

def main():
    print("==========================================================")
    print("   IBM QUANTUM CLOUD: ENVIO PARA HARDWARE FÍSICO")
    print("==========================================================")
    
    # 1. Autenticação Segura
    try:
        service = QiskitRuntimeService()
        print("[+] Credenciais da IBM encontradas no computador.")
    except Exception:
        print("[!] Nenhuma credencial da IBM foi encontrada.")
        print("-> Crie sua conta em: https://quantum.ibm.com/")
        print("-> Copie seu 'API Token' no painel principal.")
        token = getpass.getpass("Cole seu IBM API Token (Ficará invisível ao digitar): ")
        
        print("\nSalvando token de forma segura...")
        QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token=token, set_as_default=True)
        service = QiskitRuntimeService()
        print("[+] Token salvo com sucesso!\n")
        
    # Busca um Computador Real que tenha os bits necessários (minimo 127) e esteja online
    print("[+] Buscando o processador quântico (QPU) mais livre...")
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=100)
    print(f"[!] HARDWARE SELECIONADO: {backend.name} ({backend.num_qubits} Qubits)")
    print(f"    Fila atual: {backend.status().pending_jobs} jobs esperando.")

    # ---------------------------------------------------------
    # CONSTRUÇÃO DO CIRCUITO (Apenas 4 bits para não abusar da nuvem grátis)
    # ---------------------------------------------------------
    n_search_bits = 1 # Reduzido ao máximo: 1 bit (0 ou 1)
    target_window = '1'
    
    x_search = QuantumRegister(n_search_bits, 'priv_key')
    ancilla_hash = QuantumRegister(1, 'ancilla_match')
    meas = ClassicalRegister(n_search_bits, 'meas_key')
    
    work_reg = QuantumRegister(n_search_bits, 'work_state')
    reg_c = QuantumRegister(n_search_bits, 'ripemd_c')
    reg_d = QuantumRegister(n_search_bits, 'ripemd_d')
    reg_res = QuantumRegister(n_search_bits, 'ripemd_res')
    
    qc = QuantumCircuit(x_search, work_reg, reg_c, reg_d, reg_res, ancilla_hash, meas)
    
    qc.h(x_search)
    qc.x(ancilla_hash)
    qc.h(ancilla_hash)
    
    iterations = math.floor((math.pi / 4) * math.sqrt(2 ** n_search_bits))
    
    add_inst = build_cuccaro_adder(n_search_bits)
    sub_inst = add_inst.inverse()
    cin = QuantumRegister(1, 'cin')
    cout = QuantumRegister(1, 'cout')
    qc.add_register(cin, cout)
    
    for _ in range(iterations):
        for idx in range(n_search_bits):
            qc.cx(x_search[idx], work_reg[idx])
        
        qc.append(add_inst, [cin[0]] + list(x_search) + list(work_reg) + [cout[0]])
        ripemd_g_func_bitwise(qc, work_reg, reg_c, reg_d, reg_res, n_search_bits)
        
        for i, bit in enumerate(reversed(target_window)):
            if bit == '0': qc.x(x_search[i])
                
        qc.mcx(x_search, ancilla_hash[0])
        
        for i, bit in enumerate(reversed(target_window)):
            if bit == '0': qc.x(x_search[i])
        
        ripemd_g_func_bitwise(qc, work_reg, reg_c, reg_d, reg_res, n_search_bits)
        qc.append(sub_inst, [cin[0]] + list(x_search) + list(work_reg) + [cout[0]])
        
        for idx in reversed(range(n_search_bits)):
            qc.cx(x_search[idx], work_reg[idx])
        
        apply_diffuser(qc, x_search)
        
    qc.measure(x_search, meas)
    
    print("\n[+] Transpilando o circuito para o mapa físico (Coupling Map) da QPU...")
    # Nível de otimização 3 (o máximo do Qiskit) para tentar reduzir o tamanho do circuito
    transpiled_circuit = transpile(qc, backend=backend, optimization_level=3)
    
    depth = transpiled_circuit.depth()
    print(f"[!] Profundidade Física do Circuito: {depth} portas lógicas")
    
    if depth > 100:
        print("    [AVISO] Profundidade extrema. O ruído quântico (decoerência) dominará o resultado.")
        
    print("\n[+] Configurando Escudos de Mitigação de Erro (DD e Twirling)...")
    options = SamplerOptions()
    options.dynamical_decoupling.enable = True
    options.dynamical_decoupling.sequence_type = "XX"
    options.twirling.enable_gates = True

    print("\n[+] Enviando Job Blindado para a nuvem da IBM...")
    sampler = Sampler(mode=backend, options=options)
    
    # Submissão (Usando o padrão V2 do Qiskit Runtime)
    job = sampler.run([transpiled_circuit], shots=1024)
    print(f"\n==========================================================")
    print(f"   JOB ENVIADO COM SUCESSO!")
    print(f"   ID do Job: {job.job_id()}")
    print(f"==========================================================")
    print("\nVocê pode acompanhar a fila de execução ao vivo pelo navegador no painel da IBM Quantum.")
    print("Quando terminar, o resultado será salvo automaticamente.")

if __name__ == "__main__":
    main()
