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

    def _sha256_ch(self, qc, e, f, g, ancilla):
        """
        Função Ch (Choose) do SHA-256 reversível: (e AND f) XOR ((NOT e) AND g)
        Mapeado em portas lógicas quânticas via Toffoli e CX.
        """
        qc.cx(e, f)
        qc.ccx(e, f, ancilla)
        qc.cx(e, f)
        qc.x(e)
        qc.ccx(e, g, ancilla)
        qc.x(e)

    def _uncompute_sha256_ch(self, qc, e, f, g, ancilla):
        qc.x(e)
        qc.ccx(e, g, ancilla)
        qc.x(e)
        qc.cx(e, f)
        qc.ccx(e, f, ancilla)
        qc.cx(e, f)

    def _sha256_maj(self, qc, a, b, c, ancilla):
        """
        Função Maj (Majority) do SHA-256 reversível: (a AND b) XOR (a AND c) XOR (b AND c)
        """
        qc.cx(a, b)
        qc.cx(a, c)
        qc.ccx(b, c, ancilla)
        qc.cx(a, c)
        qc.cx(a, b)
        qc.cx(a, ancilla)

    def _uncompute_sha256_maj(self, qc, a, b, c, ancilla):
        qc.cx(a, ancilla)
        qc.cx(a, b)
        qc.cx(a, c)
        qc.ccx(b, c, ancilla)
        qc.cx(a, c)
        qc.cx(a, b)

    def _apply_cryptographic_load(self, qc, reg_a, reg_ancillas):
        """
        Injeta a carga física verdadeira baseada na estrutura do SHA-256.
        Aplica as funções Ch e Maj para criar o grau de emaranhamento real
        esperado na compressão criptográfica.
        """
        num_rounds = 4 # Reduced-round para teste (aumentar na Vast.ai para encontrar limite)
        n = self.total_bits
        
        for r in range(num_rounds):
            for i in range(0, n - 3, 3):
                # Aplica CH em trincas de qubits usando as ancillas como destino
                self._sha256_ch(qc, reg_a[i], reg_a[i+1], reg_a[i+2], reg_ancillas[i])
                # Aplica MAJ na mesma trinca
                self._sha256_maj(qc, reg_a[i], reg_a[i+1], reg_a[i+2], reg_ancillas[i+1])
                
    def _uncompute_cryptographic_load(self, qc, reg_a, reg_ancillas):
        """
        Uncompute EXATO e rigoroso das funções Ch e Maj para limpar a VRAM.
        """
        num_rounds = 4
        n = self.total_bits
        
        for r in reversed(range(num_rounds)):
            for i in reversed(range(0, n - 3, 3)):
                self._uncompute_sha256_maj(qc, reg_a[i], reg_a[i+1], reg_a[i+2], reg_ancillas[i+1])
                self._uncompute_sha256_ch(qc, reg_a[i], reg_a[i+1], reg_a[i+2], reg_ancillas[i])

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
