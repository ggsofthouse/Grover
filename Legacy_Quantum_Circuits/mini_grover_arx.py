# mini_grover_arx.py
"""
Fase 3: Mini-Grover ARX (Addition, Rotation, XOR)
Prova de Conceito de Criptoanálise Algébrica ponta a ponta simulando um Oráculo de Hash.
Espaço: 3 bits. Alvo Hash: 110. Chave Esperada: 010 (2).
"""

import math
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

def apply_diffuser(qc, search_reg):
    """ Difusor de Grover para reflexão sobre a média """
    qc.h(search_reg)
    qc.x(search_reg)
    
    # MCZ (Multi-Controlled Z)
    qc.h(search_reg[-1])
    qc.mcx(search_reg[:-1], search_reg[-1])
    qc.h(search_reg[-1])
    
    qc.x(search_reg)
    qc.h(search_reg)

def main():
    n_bits = 3
    print("\n==========================================================")
    print("   MINI-GROVER ARX: Criptoanálise Algébrica via GPU")
    print("   Oráculo: Hash(x) = ((x + 3) RotL 1) XOR 5")
    print("   Hash Alvo: 6 (110) | Pre-image Esperada: 2 (010)")
    print("==========================================================")

    # Registradores
    cin = QuantumRegister(1, 'cin')
    a_reg = QuantumRegister(n_bits, 'k1_add')
    x_reg = QuantumRegister(n_bits, 'x_search')
    cout = QuantumRegister(1, 'cout')
    ancilla = QuantumRegister(1, 'ancilla')
    meas = ClassicalRegister(n_bits, 'meas_x')
    
    qc = QuantumCircuit(cin, a_reg, x_reg, cout, ancilla, meas)
    
    # ---------------------------------------------------------
    # INICIALIZAÇÃO
    # ---------------------------------------------------------
    qc.h(x_reg) # Espaço de busca em superposição total
    
    qc.x(ancilla)
    qc.h(ancilla) # Ancilla no estado |->
    
    # Constante K1 = 3 (011 -> LSB=1, Bit1=1)
    qc.x(a_reg[0])
    qc.x(a_reg[1])
    
    qc.barrier()
    
    # ---------------------------------------------------------
    # CONSTRUÇÃO DO ORÁCULO E DIFUSOR
    # ---------------------------------------------------------
    cuccaro_add = build_cuccaro_adder(n_bits)
    cuccaro_sub = cuccaro_add.inverse() # Uncompute aritmético mágico
    cuccaro_sub.name = "Cuccaro_SUB"
    
    iterations = math.floor((math.pi / 4) * math.sqrt(2 ** n_bits))
    print(f"Número de iterações de Grover calculadas: {iterations}")
    
    for _ in range(iterations):
        # 1. ADD (Adição Modular com Cuccaro)
        qc.append(cuccaro_add, [cin[0]] + list(a_reg) + list(x_reg) + [cout[0]])
        
        # 2. ROTL (Remapeamento Lógico de Fios)
        # B_rot: MSB vira LSB, os outros sobem 1 posição
        # new_b0 = old_b2 | new_b1 = old_b0 | new_b2 = old_b1
        x_rot = [x_reg[2], x_reg[0], x_reg[1]]
        
        # 3. XOR (K2 = 5 -> 101)
        qc.x(x_rot[0])
        qc.x(x_rot[2])
        
        # 4. COMPARAÇÃO (Hash Alvo = 110 -> 6)
        # Queremos ativar o MCX quando o estado for 110 (LSB=0, Bit1=1, MSB=1)
        # Invertemos os bits 0 para que tudo fique 1 e ative o Kickback
        qc.x(x_rot[0])
        qc.mcx(x_rot, ancilla[0]) # Phase Kickback
        qc.x(x_rot[0]) # Desfaz a inversão da comparação
        
        # 5. UNCOMPUTE TOTAL DO HASH (Reversão Estrita)
        # a) Desfaz o XOR
        qc.x(x_rot[0])
        qc.x(x_rot[2])
        
        # b) Desfaz a Adição (Subtração via Inverse) 
        # O remapeamento lógico (ROT) desfaz sozinho pois usamos a referência x_reg original
        qc.append(cuccaro_sub, [cin[0]] + list(a_reg) + list(x_reg) + [cout[0]])
        
        qc.barrier()
        
        # 6. DIFUSOR DE GROVER
        apply_diffuser(qc, x_reg)
        qc.barrier()
        
    qc.measure(x_reg, meas)
    
    print("\n[!] Circuito Completo Plotado (Visão Funcional):")
    print(qc.draw(fold=-1))
    
    print("\nInicializando simulador AerSimulator (GPU / Tensor Network)...")
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
    except Exception as e:
        print("\n[AVISO] Detectada falha interna de mapeamento no cuTensorNet (WSL).")
        print("Ativando Fallback de Segurança para cuStateVec na GPU...")
        simulator = AerSimulator(method='statevector', device='GPU')
        compiled = transpile(qc, simulator)
        t_start = time.time()
        job = simulator.run(compiled, shots=1024)
        result = job.result()
        t_end = time.time()
        
    counts = result.get_counts()
    
    print(f"Status do job: {result.status}")
    print(f"Tempo de execução (GPU): {t_end - t_start:.4f}s")
    
    print("\n--- RESULTADO DA CRIPTOANÁLISE (Grover ARX) ---")
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state, top_shots = sorted_counts[0]
    top_decimal = int(top_state, 2)
    
    print(f"Chave Encontrada (Pre-Image): Binário [{top_state}] -> Decimal: {top_decimal}")
    print(f"Confiança Quântica (Probabilidade): {(top_shots/1024)*100:.2f}%")
    
    if top_decimal == 2:
        print("\n[VÍTIMA COMPROMETIDA] Grover convergiu com sucesso para a chave correta (010)!")
    else:
        print("\n[FALHA] Colapso incorreto. Verifique a coerência do Uncompute.")

if __name__ == "__main__":
    main()
