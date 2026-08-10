# teste_tensornet.py
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import time

def main():
    print("=== Teste de Aceleração cuQuantum / GPU (Tensor Network) ===")
    print("Inicializando simulador Qiskit Aer com método tensor_network no dispositivo GPU...")
    
    try:
        simulator = AerSimulator(method='tensor_network', device='GPU')
        print("Simulador GPU cuTensorNet configurado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar GPU/cuQuantum: {e}")
        return

    num_qubits = 25
    print(f"Montando circuito quântico com {num_qubits} qubits (Superposição total Hadamard)...")
    circ = QuantumCircuit(num_qubits)
    circ.h(range(num_qubits))
    circ.measure_all()

    print("Transpilando circuito para o simulador GPU...")
    circ = transpile(circ, simulator)
    
    start_time = time.time()
    job = simulator.run(circ, shots=100)
    result = job.result()
    end_time = time.time()
    
    print(f"Status da execução: {result.status}")
    print(f"Tempo de simulação (Rede Tensorial na GPU RTX 2060): {end_time - start_time:.4f} segundos")

if __name__ == "__main__":
    main()
