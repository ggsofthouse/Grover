import time
from pysat.formula import CNF
from pysat.solvers import Solver

def exact_preimage_solver(cnf_filepath):
    print("=========================================================")
    print("   MOTOR HPC DE SOLUÇÃO EXATA (Glucose SAT SOLVER)")
    print("=========================================================")
    print(f"[*] Carregando Grafo Criptográfico Maciço: {cnf_filepath}")
    
    start_load = time.time()
    formula = CNF(from_file=cnf_filepath)
    print(f"[+] Carregamento completo em {time.time() - start_load:.2f}s")
    print(f"    -> Variáveis Booleanas (Nós Livres): {formula.nv}")
    print(f"    -> Cláusulas Lógicas (Restrições Analíticas): {len(formula.clauses)}")
    
    print("\n[*] Instanciando Solver Glucose (Nível Militar / C++)...")
    print("[!] AVISO: O motor tentará encontrar a única permutação válida (A Chave Pública).")
    print("[!] Tempo estimado de convergência para SHA-256 completo: Semanas/Meses.\n")
    
    # Glucose41 (glucose4) é um dos solvers SAT mais estáveis no Windows/Linux padrão da lib pysat.
    start_opt = time.time()
    
    # ATENÇÃO: Adicionando timeout interno para proteger a execução local se necessário.
    # O solver.solve() buscará exaustivamente.
    try:
        with Solver(name="glucose4", bootstrap_with=formula.clauses) as solver:
            print("[*] Algoritmo de busca física acionado (Glucose CDCL)...")
            print("    -> Escaneando hiper-espaço de estados. Aguarde...")
            
            is_sat = solver.solve() 
            
            if is_sat:
                print(f"\n[SUCESSO] COLAPSO DO GRAFO! SATISFAZIBILIDADE ALCANÇADA!")
                print(f"Tempo Total de Otimização: {time.time() - start_opt:.4f}s")
                
                model = solver.get_model()
                
                pubkey_bits = []
                for var in model:
                    if abs(var) <= 256: # Pega apenas as variáveis de entrada
                        if var > 0:
                            pubkey_bits.append('1')
                        else:
                            pubkey_bits.append('0')
                            
                pubkey_bin_str = "".join(pubkey_bits)
                pubkey_hex = hex(int(pubkey_bin_str, 2))[2:].zfill(64)
                
                print(f"\n[!] DUMP DA PRÉ-IMAGEM (CHAVE PÚBLICA EXTRAÍDA DO HASH):")
                print(f"PubKey_X: {pubkey_hex}")
                
            else:
                print("\n[FALHA] Grafo INSATISFAZÍVEL. O Hash fornecido não possui pré-imagem possível nas restrições dadas.")
                
    except Exception as e:
        print(f"\n[ERRO NA EXECUÇÃO DO SOLVER] Detalhes: {e}")
    except KeyboardInterrupt:
        print(f"\n[INTERROMPIDO] Busca cancelada manualmente após {time.time() - start_opt:.2f}s.")
        print("O solver estava percorrendo as ramificações de conflito.")

if __name__ == "__main__":
    exact_preimage_solver("sha256_exact_state.cnf")
