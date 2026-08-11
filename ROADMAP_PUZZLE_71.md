# ROADMAP DE ESCALONAMENTO: BITCOIN PUZZLE 71

Este documento estabelece as diretrizes arquiteturais e limites físicos para escalar a quebra do Bitcoin Puzzle (via Oráculo Grover e Redes Tensoriais) do baseline atual (Puzzle 20) para o alvo de produção (Puzzle 71).

## 1. O Abismo da Complexidade Matemática
O algoritmo de Grover escala com a raiz quadrada do espaço de busca.
- **Puzzle 20:** $2^{20}$ chaves -> $\approx 1.000$ iterações de Grover.
- **Puzzle 71:** $2^{71}$ chaves -> $\approx 4.3$ Bilhões de iterações de Grover.

Simular 4.3 Bilhões de iterações do SHA-256 em um único grafo tensorial exato (sem poda) exige uma memória VRAM e um tempo de Path Finding que não existem no plano físico atual. Para atingir o Puzzle 71, precisamos de estratégias arquiteturais em HPC (High Performance Computing).

## 2. Estratégias de Escalonamento

### 2.1. Abordagem Híbrida (ASIC + Sub-rotina Quântica) - [Estratégia Recomendada]
Nesta abordagem, não simulamos os 71 bits de uma vez. O ganho quântico é usado como uma "Sub-rotina de Colapso Rápido" acoplada a uma busca clássica (CPU/GPU/ASIC).

- **Como Funciona:** 
  1. Fixamos classicamente os $41$ bits superiores do range (como um "chute" de um minerador clássico).
  2. Sobram $30$ bits. Injetamos essa janela no simulador (Qiskit + cuTensorNet).
  3. A A100/cluster resolve os 30 bits simultaneamente (apenas $\approx 32.700$ iterações de Grover).
  4. Se o Oráculo colapsar sem encontrar o Hash, a CPU avança os 41 bits superiores e repete.
- **Poder Computacional Clássico Necessário:** O esforço clássico é reduzido a apenas $2^{41}$ (2.1 Trilhões de hashes), um número trivial para qualquer farm ASIC moderno.

### 2.2. Poda de Tensores (Approximated Tensor Networks)
Para que a RAM e a VRAM não explodam com iterações profundas, usamos a limitação de *Bond Dimension* (poda de probabilidade).

- **Como Funciona:** Em vez de contrações exatas (que preservam 100% dos ramos matemáticos), instruímos o cuTensorNet a cortar matrizes de baixa probabilidade.
- **Impacto:** A taxa de confiança do Oráculo cai de $\approx 97\%$ para algo entre $10\%$ a $20\%$ (Tornando o simulador *lossy*).
- **Vantagem:** O tamanho da Rede Tensorial fica artificialmente congelado, permitindo simular o Puzzle 71 quase inteiro na GPU, repetindo a execução várias vezes até a probabilidade acerta convergir.

### 2.3. SuperPOD Distribuído (MPI)
Força bruta em escala governamental. Reativamos a configuração `CUTENSORNET_COMMUNICATOR_CONFIG=1` em clusters dedicados.

- **Como Funciona:** Uma rede InfiniBand conecta 16x, 64x ou 128x placas NVIDIA A100 ou H100.
- O grafo quântico é particionado fisicamente através da rede. Para 16x A100 (80GB), obtemos $1.28$ TB de VRAM unificada, permitindo janelas nativas de 35 a 40 bits com contração exata.

## 3. Próximos Passos Imediatos no Código
1. **Validar Fronteira de Slicing:** Achar o limite exato de bits em 1x A100 (Teste atual: 6 a 10 bits).
2. **Implementar MPS/PEPS (Poda):** Modificar `puzzle20_validador.py` injetando tolerância a perdas (max bond dimension) para esticar a janela.
3. **Loop Híbrido:** Escrever o invólucro em Python que itera bits clássicos enquanto invoca o núcleo TensorNetwork apenas para os bits inferiores.
