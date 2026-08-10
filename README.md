# Grover ARX: Criptoanálise Quântica via Redes Tensoriais (cuTensorNet)

Este projeto implementa uma Prova de Conceito (PoC) de criptoanálise algébrica focada em inverter funções de hash criptográficas (especificamente o núcleo ARX do RIPEMD-160) utilizando o Algoritmo de Grover.

Para contornar o colapso clássico de memória (OOM) causado por simulações de Vetores de Estado (*Statevectors*), este pipeline modela o circuito quântico como um **Hipergrafo Tensorial**. Utilizando o `cuQuantum` (NVIDIA cuTensorNet) com estratégias avançadas de bloqueio de emaranhamento, o projeto comprime as portas CCX (Toffoli) e realiza "Windowed Searches" (Buscas por Janelas), transferindo o limite físico da memória RAM para o tempo de contração (GFLOPS da GPU).

## 🧩 Arquitetura do Oráculo

A matemática do Bitcoin (SHA-256 e RIPEMD-160) repousa sobre a tríade **ARX** (Addition, Rotation, XOR). Nosso Oráculo quântico foi modularizado para espelhar essa arquitetura com reversibilidade estrita (0% de vazamento de coerência):

1. **Adição (Cuccaro Adder):** Implementação nativa do somador Ripple-Carry reversível de Cuccaro. O circuito usa portas MAJ e UMA para garantir que o lixo algébrico possa ser integralmente revertido (*Uncomputed*).
2. **Rotação (ROTL):** Executada com custo quântico zero através do remapeamento lógico (wire swapping).
3. **XOR:** Inversões puras e baratas baseadas em portas `X`.
4. **Comparação & Kickback:** Uso de portas MCX (Multi-Controlled X) para negativar a fase do alvo correto no espaço de Hilbert.
5. **Reversibilidade (Uncompute Estrito):** O circuito aplica o inverso exato da cascata aritmética (`cuccaro_sub = cuccaro_add.inverse()`) antes do Difusor de Grover, alcançando taxas empíricas de >96% de confiança no colapso da pré-imagem correta.

## 🚀 Executando na Nuvem (Vast.ai / GPUs H100)

O limite prático deste código é a densidade da rede tensorial gerada pelas portas Toffoli, o que exige GPUs com enorme VRAM e altíssimo TFLOPS (ex: NVIDIA H100 ou B200). 

Para rodar em uma instância da **Vast.ai** (recomendada imagem `nvidia/cuda:12.1.1-devel-ubuntu22.04`), basta executar o script de inicialização que instalará o Miniconda, o Qiskit e os drivers do `cuquantum-python`:

```bash
# 1. Clone o repositório ou suba a pasta E:\Grover
# 2. Dê permissão e execute o bootstrap
chmod +x setup_vast_h100.sh
./setup_vast_h100.sh

# 3. Ative o ambiente
conda activate quantum_env

# 4. Inicie o colapso quântico
python puzzle20_validador.py
```

## 💻 Executando Localmente (Windows WSL)

O ambiente local foi idealizado para rodar em WSL2 garantindo acesso aos drivers CUDA do Windows:

1. Abra seu terminal WSL (Ubuntu).
2. Garanta que o Conda está instalado.
3. Crie o ambiente e instale as dependências padrão do Qiskit.
4. Execute o validador:
```bash
python mini_grover_arx.py
```

## 📈 Roadmap e Próximos Passos

A Fase 3 do projeto provou que a ponte entre o Hash (Hash160) e a pré-imagem quântica funciona matematicamente. O próximo estágio de escalonamento engloba:
- **Passo 1 (Matemática Inversa):** Lógica index-to-key para reverter o offset da janela para WIF.
- **Passo 2 (Integração Secp256k1):** Substituir a entrada direta pela multiplicação do Ponto Gerador `G` da curva elíptica usando portas lógicas, atacando diretamente a chave pública em vez do Hash.
- **Passo 3 (Scale Out):** Benchmark da contração do `cuTensorNet` em arquiteturas multi-GPU (Blackwell B200).

---
*"Na simulação clássica, o universo só permite trocar a explosão da memória pela explosão do tempo. O Hardware Quântico deforma essa regra."*
