import time
import numpy as np
import tensornetwork as tn
from pysat.formula import CNF

def cnf_to_tensor_network(cnf_filepath):
    """
    Motor Mapeador de Tensores.
    Converte um arquivo DIMACS CNF (Grafo Booleano) em uma Rede Tensorial (Tensor Network).
    Cada cláusula SAT se torna um tensor com restrições lógicas.
    """
    print(f"[*] Carregando Grafo Lógico: {cnf_filepath}")
    formula = CNF(from_file=cnf_filepath)
    
    # Descobre o número total de variáveis no grafo
    num_vars = formula.nv
    print(f"[+] Total de Variáveis Booleanas detectadas: {num_vars}")
    print(f"[+] Total de Cláusulas (Equações): {len(formula.clauses)}")
    
    # Configura o TensorNetwork para usar NumPy como backend (Motor Local de Teste)
    # Na Vast.ai, o backend será mudado para JAX ou CuPy interligado com cuTensorNet.
    tn.set_default_backend("numpy")
    
    nodes = []
    
    print("[*] Instanciando Malha Tensorial Dimensional...")
    start_time = time.time()
    
    # Iteração simplificada para o motor base:
    # Para transformar uma fórmula CNF em um Tensor Network puro,
    # associamos cada variável a um índice de dimensão 2 (bits 0 e 1).
    # A estrutura final para a Chave Pública exige a indexação exata das pontas soltas.
    
    # Criamos um "nó" tensor para cada cláusula do Hashing
    for i, clause in enumerate(formula.clauses):
        # A dimensão geométrica do tensor é dada pelo número de variáveis na cláusula
        shape = tuple([2] * len(clause))
        
        # Inicializamos com 1.0 (Verdadeiro)
        tensor_data = np.ones(shape, dtype=np.float32)
        
        # A condição de insatisfabilidade: 
        # A única combinação que faz a cláusula ser Falsa é quando todas as literais são falsas.
        # Definimos essa coordenada específica na matriz como 0.0
        false_index = []
        for literal in clause:
            if literal > 0:
                false_index.append(0) # Se a variável é pura, ela tem que ser 0 para ser falsa
            else:
                false_index.append(1) # Se a variável é negada, ela tem que ser 1 para ser falsa
                
        tensor_data[tuple(false_index)] = 0.0
        
        # Cria o Nó Tensorial Físico
        node = tn.Node(tensor_data, name=f"Clause_{i}")
        nodes.append(node)
        
    print(f"[SUCESSO] Rede Tensorial Instanciada em {time.time() - start_time:.4f}s")
    print(f"    -> {len(nodes)} Tensores Geométricos ancorados na memória.")
    print("    -> Rede pronta para otimização variazional (Exact Pre-image Finder).")
    
    return nodes

if __name__ == "__main__":
    print("=========================================================")
    print("   MAPEADOR TENSORIAL - (CNF TO TENSOR NETWORK)")
    print("=========================================================")
    
    # Lê o arquivo exportado pelo Passo 1
    cnf_file = "puzzle20_hash.cnf"
    
    try:
        nodes = cnf_to_tensor_network(cnf_file)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo {cnf_file} não encontrado. Rode o script 1_sat_generator_real.py primeiro.")
