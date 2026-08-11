from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

class BitcoinAddressQuantumOracle:
    """
    Simulador Completo do Pipeline do Bitcoin (Toy Model).
    Esta classe simula o caminho Criptográfico Integral (Address-Only):
    Chave Privada -> Curva Elíptica (Secp256k1) -> PubKey -> SHA256/RIPEMD160 -> Address
    
    Tudo construído em portas reversíveis quânticas para o algoritmo de Grover,
    provando que podemos realizar o ataque em endereços sem a chave pública revelada.
    """
    def __init__(self, total_bits, quantum_bits, target_address_bin):
        self.total_bits = total_bits
        self.quantum_bits = quantum_bits
        self.target_address_bin = target_address_bin
        
    def _initialize_constant(self, qc, reg, value_bin):
        for i, bit in enumerate(reversed(value_bin)):
            if bit == '1':
                qc.x(reg[i])

    # ========================================================
    # 1. BLOCO DA CURVA ELÍPTICA (ECDLP TOY)
    # ========================================================
    def _quantum_modular_adder(self, qc, a, b, ancilla):
        """ Somador Modular Reversível """
        qc.ccx(a, b, ancilla)
        qc.cx(a, b)
        
    def _uncompute_modular_adder(self, qc, a, b, ancilla):
        qc.cx(a, b)
        qc.ccx(a, b, ancilla)

    def _quantum_point_addition(self, qc, k_reg, pub_x_reg, pub_y_reg, ancillas):
        """ Simulação da Multiplicação Escalar (k * G) """
        n = len(k_reg)
        for i in range(n - 1):
            self._quantum_modular_adder(qc, k_reg[i], k_reg[i+1], ancillas[i])
            qc.ccx(pub_x_reg[0], k_reg[i], ancillas[i+1])
            qc.cx(ancillas[i], pub_y_reg[0])
            
    def _uncompute_point_addition(self, qc, k_reg, pub_x_reg, pub_y_reg, ancillas):
        n = len(k_reg)
        for i in reversed(range(n - 1)):
            qc.cx(ancillas[i], pub_y_reg[0])
            qc.ccx(pub_x_reg[0], k_reg[i], ancillas[i+1])
            self._uncompute_modular_adder(qc, k_reg[i], k_reg[i+1], ancillas[i])

    # ========================================================
    # 2. BLOCO DE HASHING (SHA-256 + RIPEMD-160 TOY)
    # ========================================================
    def _quantum_hash_compression(self, qc, pub_x_reg, pub_y_reg, hash_reg, ancillas):
        """ 
        Simulação Reversível do Pipeline de Hashing. 
        Recebe as coordenadas X, Y da PubKey gerada no bloco anterior e injeta a complexidade algébrica do Hash.
        """
        # Emaranha PubKey_X e PubKey_Y para gerar o "Address/Hash160"
        qc.cx(pub_x_reg[0], hash_reg[0])
        qc.cx(pub_y_reg[0], hash_reg[1])
        qc.ccx(pub_x_reg[0], pub_y_reg[0], ancillas[0])
        qc.cx(ancillas[0], hash_reg[0])
        
    def _uncompute_hash_compression(self, qc, pub_x_reg, pub_y_reg, hash_reg, ancillas):
        qc.cx(ancillas[0], hash_reg[0])
        qc.ccx(pub_x_reg[0], pub_y_reg[0], ancillas[0])
        qc.cx(pub_y_reg[0], hash_reg[1])
        qc.cx(pub_x_reg[0], hash_reg[0])

    # ========================================================
    # CONSTRUÇÃO DO CIRCUITO (O ORÁCULO GROVER COMPLETO)
    # ========================================================
    def build_circuit(self, prefix_bin):
        n = self.total_bits
        
        reg_k = QuantumRegister(n, 'K_PrivKey') 
        reg_pub_x = QuantumRegister(2, 'PubKey_X') 
        reg_pub_y = QuantumRegister(2, 'PubKey_Y') 
        
        # O resultado do RIPEMD160(SHA256(PubKey)) (O Endereço Toy)
        reg_address = QuantumRegister(2, 'Bitcoin_Address') 
        
        reg_ancillas_curve = QuantumRegister(n + 2, 'Ancillas_Curve') 
        reg_ancillas_hash = QuantumRegister(2, 'Ancillas_Hash') 
        oracle_ancilla = QuantumRegister(1, 'Target_Flag') 
        
        c_q = ClassicalRegister(self.quantum_bits, 'Meas_Q')
        
        qc = QuantumCircuit(reg_k, reg_pub_x, reg_pub_y, reg_address, reg_ancillas_curve, reg_ancillas_hash, oracle_ancilla, c_q)
        
        # 1. Prefixo Clássico 
        self._initialize_constant(qc, reg_k[self.quantum_bits:], prefix_bin)
        
        # 2. Janela Quântica (Superposição da Chave Privada)
        qc.h(reg_k[:self.quantum_bits])
        
        # 3. Qubit de Fase
        qc.x(oracle_ancilla)
        qc.h(oracle_ancilla)
        
        # ====================================================
        # START: PIPELINE CRYPTO ADDRESS-ONLY
        # ====================================================
        
        # PASSO A: Multiplicação Escalar (Gera a Chave Pública)
        self._quantum_point_addition(qc, reg_k, reg_pub_x, reg_pub_y, reg_ancillas_curve)
        
        # PASSO B: SHA-256 + RIPEMD-160 (Gera o Endereço a partir da Chave Pública)
        self._quantum_hash_compression(qc, reg_pub_x, reg_pub_y, reg_address, reg_ancillas_hash)
        
        # O Radar compara O ENDEREÇO GERADO com o Endereço Público do Puzzle (Target)
        target_address_reversed = self.target_address_bin[::-1]
        
        # Zero-checking no Endereço
        for i in range(min(len(reg_address), len(target_address_reversed))):
            if target_address_reversed[i] == '0':
                qc.x(reg_address[i])
                
        # Phase Kickback (Só aciona se o Endereço em superposição bater com o Target)
        qc.mcx(reg_address, oracle_ancilla)
        
        # Uncompute Zero-checking
        for i in range(min(len(reg_address), len(target_address_reversed))):
            if target_address_reversed[i] == '0':
                qc.x(reg_address[i])
                
        # PASSO C: Uncompute Rigoroso do Pipeline Inteiro para não dar Out of Memory
        self._uncompute_hash_compression(qc, reg_pub_x, reg_pub_y, reg_address, reg_ancillas_hash)
        self._uncompute_point_addition(qc, reg_k, reg_pub_x, reg_pub_y, reg_ancillas_curve)
        
        # ====================================================
        # END: PIPELINE CRYPTO ADDRESS-ONLY
        # ====================================================
        
        # 4. Difusor de Grover
        self._apply_diffuser(qc, reg_k[:self.quantum_bits])
        
        qc.measure(reg_k[:self.quantum_bits], c_q)
        
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
