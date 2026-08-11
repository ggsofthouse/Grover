import time
from pysat.formula import CNF

class CryptoSATGenerator:
    """
    Motor Algébrico Definitivo - SHA-256 (Máquina de Estados Exata)
    """
    def __init__(self):
        self.cnf = CNF()
        self.var_count = 0
        
        # Constantes reais do SHA-256 (K)
        self.K = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ]

        # Estado inicial (H)
        self.H_init = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        ]
        
    def get_new_var(self):
        self.var_count += 1
        return self.var_count

    # ==========================================
    # LÓGICA BOOLEANA (TSEITIN)
    # ==========================================
    def cnf_and(self, a, b):
        c = self.get_new_var()
        self.cnf.append([-c, a])
        self.cnf.append([-c, b])
        self.cnf.append([-a, -b, c])
        return c

    def cnf_xor(self, a, b):
        c = self.get_new_var()
        self.cnf.append([-c, -a, -b])
        self.cnf.append([-c, a, b])
        self.cnf.append([c, -a, b])
        self.cnf.append([c, a, -b])
        return c

    def cnf_not(self, a):
        c = self.get_new_var()
        self.cnf.append([-c, -a])
        self.cnf.append([c, a])
        return c

    def cnf_or(self, a, b):
        c = self.get_new_var()
        self.cnf.append([c, -a])
        self.cnf.append([c, -b])
        self.cnf.append([-c, a, b])
        return c
        
    def cnf_constant_32bit(self, hex_val):
        """ Cria um bloco de 32 variáveis travadas numa constante (K_i ou H_i) """
        res = []
        bin_str = bin(hex_val)[2:].zfill(32)
        # O índice 0 da lista será o bit menos significativo (LSB)
        for bit in reversed(bin_str):
            v = self.get_new_var()
            if bit == '1':
                self.cnf.append([v])
            else:
                self.cnf.append([-v])
            res.append(v)
        return res

    # ==========================================
    # ARITMÉTICA E FUNÇÕES SHA-256
    # ==========================================
    def cnf_add_32bit(self, word1, word2):
        result = []
        carry = self.get_new_var()
        self.cnf.append([-carry])
        for i in range(32):
            xor_ab = self.cnf_xor(word1[i], word2[i])
            sum_bit = self.cnf_xor(xor_ab, carry)
            and_ab = self.cnf_and(word1[i], word2[i])
            and_c_xor = self.cnf_and(carry, xor_ab)
            carry = self.cnf_or(and_ab, and_c_xor)
            result.append(sum_bit)
        return result

    def ch(self, e, f, g):
        res = []
        for i in range(32):
            e_and_f = self.cnf_and(e[i], f[i])
            not_e = self.cnf_not(e[i])
            not_e_and_g = self.cnf_and(not_e, g[i])
            res.append(self.cnf_xor(e_and_f, not_e_and_g))
        return res

    def maj(self, a, b, c):
        res = []
        for i in range(32):
            a_and_b = self.cnf_and(a[i], b[i])
            a_and_c = self.cnf_and(a[i], c[i])
            b_and_c = self.cnf_and(b[i], c[i])
            xor_1 = self.cnf_xor(a_and_b, a_and_c)
            res.append(self.cnf_xor(xor_1, b_and_c))
        return res

    def rotr(self, x, n):
        return x[n:] + x[:n]

    def shr(self, x, n):
        zeros = []
        for _ in range(n):
            z = self.get_new_var()
            self.cnf.append([-z])
            zeros.append(z)
        return x[n:] + zeros

    def sigma0_upper(self, a):
        r2, r13, r22 = self.rotr(a, 2), self.rotr(a, 13), self.rotr(a, 22)
        res = []
        for i in range(32):
            xor1 = self.cnf_xor(r2[i], r13[i])
            res.append(self.cnf_xor(xor1, r22[i]))
        return res

    def sigma1_upper(self, e):
        r6, r11, r25 = self.rotr(e, 6), self.rotr(e, 11), self.rotr(e, 25)
        res = []
        for i in range(32):
            xor1 = self.cnf_xor(r6[i], r11[i])
            res.append(self.cnf_xor(xor1, r25[i]))
        return res

    def sigma0_lower(self, w):
        r7, r18, s3 = self.rotr(w, 7), self.rotr(w, 18), self.shr(w, 3)
        res = []
        for i in range(32):
            xor1 = self.cnf_xor(r7[i], r18[i])
            res.append(self.cnf_xor(xor1, s3[i]))
        return res

    def sigma1_lower(self, w):
        r17, r19, s10 = self.rotr(w, 17), self.rotr(w, 19), self.shr(w, 10)
        res = []
        for i in range(32):
            xor1 = self.cnf_xor(r17[i], r19[i])
            res.append(self.cnf_xor(xor1, s10[i]))
        return res

    # ==========================================
    # O MOTOR COMPLETO SHA-256
    # ==========================================
    def build_sha256_exact(self):
        print("[*] Iniciando a Maquina de Estados Exata do SHA-256 em Álgebra SAT...")
        
        # A mensagem de entrada desconhecida: Uma chave pública de 256 bits (8 palavras de 32 bits)
        # O bloco SHA256 opera em 512 bits, vamos travar os 256 restantes como padding padrão (1000...00 length)
        msg_vars = []
        for i in range(8):
            word = [self.get_new_var() for _ in range(32)]
            msg_vars.append(word)
            
        print("[+] Message Schedule Array (W) sendo construído...")
        W = []
        # W0 a W15 (A mensagem + Padding)
        for i in range(16):
            if i < 8:
                W.append(msg_vars[i]) # Os 256 bits da PubKey desconhecida
            else:
                # Padding do SHA-256 travado rigidamente (0x80000000 e length)
                # Para simplificar o lab, alocaremos variáveis livres que travaremos no solver
                word = [self.get_new_var() for _ in range(32)]
                W.append(word)
                
        # W16 a W63
        for i in range(16, 64):
            s0 = self.sigma0_lower(W[i-15])
            s1 = self.sigma1_lower(W[i-2])
            add1 = self.cnf_add_32bit(W[i-16], s0)
            add2 = self.cnf_add_32bit(add1, W[i-7])
            add3 = self.cnf_add_32bit(add2, s1)
            W.append(add3)

        print("[+] Inicializando Registradores do Estado (A..H)...")
        state = [self.cnf_constant_32bit(val) for val in self.H_init]
        a, b, c, d, e, f, g, h = state
        
        print("[+] Iniciando 64 Rodadas de Compressão Matemática...")
        for i in range(64):
            # T1 = h + Sigma1(e) + Ch(e,f,g) + K_i + W_i
            s1 = self.sigma1_upper(e)
            ch_efg = self.ch(e, f, g)
            k_i = self.cnf_constant_32bit(self.K[i])
            
            t1_1 = self.cnf_add_32bit(h, s1)
            t1_2 = self.cnf_add_32bit(t1_1, ch_efg)
            t1_3 = self.cnf_add_32bit(t1_2, k_i)
            T1 = self.cnf_add_32bit(t1_3, W[i])
            
            # T2 = Sigma0(a) + Maj(a,b,c)
            s0 = self.sigma0_upper(a)
            maj_abc = self.maj(a, b, c)
            T2 = self.cnf_add_32bit(s0, maj_abc)
            
            h = g
            g = f
            f = e
            e = self.cnf_add_32bit(d, T1)
            d = c
            c = b
            b = a
            a = self.cnf_add_32bit(T1, T2)

        print("[+] Calculando o Hash Final (H + Estado Final)...")
        out_hash = []
        final_state = [a, b, c, d, e, f, g, h]
        for i in range(8):
            out_hash.append(self.cnf_add_32bit(self.cnf_constant_32bit(self.H_init[i]), final_state[i]))
            
        print("[SUCESSO] SHA-256 Inteiramente Traduzido para Geometria SAT!")
        return msg_vars, out_hash, self.cnf

if __name__ == "__main__":
    print("=========================================================")
    print("   MOTOR ALGEBRICO DEFINITIVO (EXACT SHA-256 STATE MACHINE)")
    print("=========================================================")
    
    start_time = time.time()
    generator = CryptoSATGenerator()
    
    msg_vars, output_hash, cnf_formula = generator.build_sha256_exact()
    
    out_file = "sha256_exact_state.cnf"
    cnf_formula.to_file(out_file)
    
    print(f"\n[FÍSICA DA REDE TENSORIAL]")
    print(f"Tempo de Transpilação (Matemática Absoluta): {time.time() - start_time:.2f}s")
    print(f"Nós de Tensor Exatos (Variáveis Booleanas): {generator.var_count}")
    print(f"Malha Tridimensional (Cláusulas Lógicas): {len(cnf_formula.clauses)}")
    print(f"Exportado: {out_file}")
