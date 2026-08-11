"""
Sandbox de Otimização: T-Count Analyzer
Transpila um circuito matemático para a base tolerante a falhas (Clifford+T) 
e mede o custo exato de Portas T, que é o gargalo da compilação quântica real.
"""

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import PassManager

def count_t_gates(circuit: QuantumCircuit, optimization_level: int = 3) -> dict:
    """
    Decompõe qualquer circuito matemático em blocos atômicos físicos (Clifford + T)
    e extrai o T-Count (Fatura pesada) e o Clifford-Count (Operações limpas).
    """
    fault_tolerant_basis = ['t', 'tdg', 'h', 's', 'sdg', 'x', 'y', 'z', 'cx']
    
    # Transpila o circuito forçando-o a usar APENAS as portas tolerantes a falhas
    transpiled_qc = transpile(
        circuit, 
        basis_gates=fault_tolerant_basis, 
        optimization_level=optimization_level,
        seed_transpiler=42 # Para resultados determinísticos
    )
    
    # Conta o inventário de portas do circuito decomposto
    gate_counts = transpiled_qc.count_ops()
    
    t_count = gate_counts.get('t', 0) + gate_counts.get('tdg', 0)
    
    # Portas Clifford são todas as outras portas de processamento
    clifford_count = sum(count for gate, count in gate_counts.items() if gate not in ['t', 'tdg', 'measure', 'barrier'])
    
    return {
        "t_count": t_count,
        "clifford_count": clifford_count,
        "total_depth": transpiled_qc.depth(),
        "qubits_used": transpiled_qc.num_qubits,
        "raw_counts": dict(gate_counts)
    }

def print_analysis(circuit_name: str, metrics: dict):
    print("=" * 60)
    print(f"[{circuit_name.upper()}] - RAIO-X DE TOLERÂNCIA A FALHAS")
    print("=" * 60)
    print(f"[*] Total de Qubits Físicos Lógicos : {metrics['qubits_used']}")
    print(f"[*] Profundidade do Circuito      : {metrics['total_depth']}")
    print("-" * 60)
    print(f"[!] CUSTO DE PORTAS T (O GARGALO) : {metrics['t_count']} Portas")
    print(f"[*] Portas Clifford (O resto)     : {metrics['clifford_count']} Portas")
    print("-" * 60)
    print(f"[*] Fatura Detalhada:")
    for gate, count in metrics['raw_counts'].items():
        print(f"    - Porta '{gate}': {count}")
    print("=" * 60)


if __name__ == "__main__":
    # Teste de Sanidade Simples: Uma única Porta Toffoli
    from qiskit.circuit.library import CCXGate
    
    print("[+] Inicializando Analisador...")
    qc_test = QuantumCircuit(3)
    qc_test.ccx(0, 1, 2)
    
    metrics = count_t_gates(qc_test)
    print_analysis("Porta Toffoli Padrão (CCX)", metrics)
