from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

class BitcoinQuantumOracle:
    def __init__(self, total_bits, quantum_bits, target_hash_bin):
        self.total_bits = total_bits
        self.quantum_bits = quantum_bits
        self.prefix_bits = total_bits - quantum_bits
        self.target_hash_bin = target_hash_bin
        
    def _initialize_constant(self, qc, reg, value_bin):
        for i, bit in enumerate(reversed(value_bin)):
            if bit == '1':
                qc.x(reg[i])

    def _apply_cryptographic_load(self, qc, reg_a, reg_ancillas):
        """
        Simula a Carga Real (Física/VRAM) de um Hash Criptográfico (SHA-256).
        Como a função Hashing gera um emaranhamento massivo, injetamos uma
        cascata densa de portas Toffoli (CCX). O 'bond dimension' do TensorNet
        vai explodir exatamente aqui, servindo de stress-test para a Vast.ai.
        """
        # Exemplo: Simulação de "Rounds" de compressão do SHA-256
        num_rounds = 4 # Número de rounds para stress test (ajustável na Fase 4)
        
        for r in range(num_rounds):
            for i in range(self.total_bits - 2):
                # Cascata Toffoli que amarra todos os qubits
                qc.ccx(reg_a[i], reg_a[i+1], reg_ancillas[i])
                qc.cx(reg_ancillas[i], reg_a[i+2])
                
    def _uncompute_cryptographic_load(self, qc, reg_a, reg_ancillas):
        """
        O Inverso Exato da carga criptográfica.
        Se isso não for perfeito, as ancillas vazam estado e a simulação de Grover falha.
        """
        num_rounds = 4
        for r in reversed(range(num_rounds)):
            for i in reversed(range(self.total_bits - 2)):
                qc.cx(reg_ancillas[i], reg_a[i+2])
                qc.ccx(reg_a[i], reg_a[i+1], reg_ancillas[i])

    def build_circuit(self, prefix_bin):
        n = self.total_bits
        
        # Registradores
        reg_a = QuantumRegister(n, 'A_Key') # A chave (Prefixo Clássico + Sufixo Quântico)
        reg_ancillas = QuantumRegister(n, 'Ancillas_Hash') # Memória para o Hash
        oracle_ancilla = QuantumRegister(1, 'Target_Flag') # Flag do Grover
        c_q = ClassicalRegister(self.quantum_bits, 'Meas_Q')
        
        qc = QuantumCircuit(reg_a, reg_ancillas, oracle_ancilla, c_q)
        
        # 1. Inicia o Prefixo Clássico (Travado pela CPU)
        self._initialize_constant(qc, reg_a[self.quantum_bits:], prefix_bin)
        
        # 2. Inicia a Janela Quântica (Superposição na GPU - Radar)
        qc.h(reg_a[:self.quantum_bits])
        
        # 3. Prepara o Qubit de Fase (Phase Kickback)
        qc.x(oracle_ancilla)
        qc.h(oracle_ancilla)
        
        # ====================================================
        # START: ORÁCULO CRIPTOGRÁFICO REAL (STRESS TEST)
        # ====================================================
        # Gera o Hash
        self._apply_cryptographic_load(qc, reg_a, reg_ancillas)
        
        # Verifica a Colisão (O Radar só acende se o HASH bater)
        # Como estamos simulando a Carga Física, amarramos o match no "target_hash" fornecido
        target_reversed = self.target_hash_bin[::-1]
        
        # Flip bits do target (Zero-checking)
        for i in range(self.quantum_bits):
            if target_reversed[i] == '0':
                qc.x(reg_a[i])
                
        # Multi-Controlled X para marcar o alvo
        qc.mcx(reg_a[:self.quantum_bits], oracle_ancilla)
        
        # Desfaz os flips (Uncompute do Zero-checking)
        for i in range(self.quantum_bits):
            if target_reversed[i] == '0':
                qc.x(reg_a[i])
                
        # Uncompute do Hash (Limpeza Rigorosa da VRAM/Ancillas)
        self._uncompute_cryptographic_load(qc, reg_a, reg_ancillas)
        # ====================================================
        # END: ORÁCULO CRIPTOGRÁFICO REAL
        # ====================================================
        
        # 4. Difusor de Grover (Apenas no sufixo quântico - Amplificação Parcial)
        self._apply_diffuser(qc, reg_a[:self.quantum_bits])
        
        # Medição do Radar
        qc.measure(reg_a[:self.quantum_bits], c_q)
        
        return qc

    def _apply_diffuser(self, qc, search_reg):
        n = len(search_reg)
        qc.h(search_reg)
        qc.x(search_reg)
        qc.h(search_reg[-1])
        if n > 1:
            qc.mcx(search_reg[:-1], search_reg[-1])
        else:
            qc.x(search_reg[-1])
        qc.h(search_reg[-1])
        qc.x(search_reg)
        qc.h(search_reg)
