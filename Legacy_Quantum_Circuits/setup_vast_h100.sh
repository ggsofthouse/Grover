#!/bin/bash
# ==============================================================================
# SETUP AUTOMATIZADO VAST.AI: GROVER TENSOR-NETWORK
# Alvo recomendado: NVIDIA H100 (SXM5) ou RTX 4090 / 6000 Ada
# Imagem Base Recomendada: nvidia/cuda:12.1.1-devel-ubuntu22.04 ou PyTorch
# ==============================================================================

set -e # Interrompe o script se ocorrer qualquer erro

echo "[+] Iniciando provisionamento do Ambiente Quântico (cuTensorNet)..."
echo "[!] Verificando hardware da GPU..."
nvidia-smi

# 1. Atualização do Sistema
echo -e "\n[+] Atualizando pacotes do sistema (Ubuntu)..."
apt-get update && apt-get install -y wget bzip2 git libgl1 htop tmux

# 2. Instalação do Miniconda (Isolamento de Ambiente)
if ! command -v conda &> /dev/null
then
    echo -e "\n[+] Instalando Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    rm miniconda.sh
    export PATH="$HOME/miniconda/bin:$PATH"
    echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> ~/.bashrc
else
    echo -e "\n[+] Conda já instalado. Pulando..."
fi

eval "$(conda shell.bash hook)"

# Aceita Termos de Serviço do Conda (Fallback)
conda config --set solver classic || true

# 3. Criação do Ambiente Quântico via conda-forge (Bypass no TOS)
echo -e "\n[+] Criando ambiente 'quantum_env' (Python 3.10)..."
conda create -y -n quantum_env -c conda-forge python=3.10
conda activate quantum_env

# 4. Instalação do NVIDIA cuQuantum (O Coração da Rede Tensorial)
echo -e "\n[+] Instalando SDK cuQuantum (Backend para Tensor Networks)..."
# É crucial amarrar na versão do CUDA da imagem da Vast.ai (assumindo CUDA 12)
pip install cuquantum-python-cu12==23.10.0

# 5. Instalação do Qiskit e Aer Simulator GPU
echo -e "\n[+] Instalando Qiskit e Aer Simulator com suporte a GPU..."
pip install qiskit==1.2.4 qiskit-aer-gpu==0.15.1

# 6. Pacotes Auxiliares
echo -e "\n[+] Instalando bibliotecas de manipulação de dados e tensores..."
pip install numpy matplotlib pandas

echo -e "\n================================================================="
echo "   [SUCESSO] AMBIENTE QUÂNTICO (TENSOR-NETWORK) PRONTO!"
echo "================================================================="
echo "Para testar a infraestrutura, execute:"
echo "1. conda activate quantum_env"
echo "2. python puzzle20_validador.py"
echo "================================================================="
