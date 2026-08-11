#!/bin/bash

echo "=========================================================="
echo "    Iniciando Setup do Ambiente - VAST.AI (RTX 4090)      "
echo "=========================================================="

# 1. Atualização do sistema e ferramentas básicas
echo "[*] Instalando dependências do sistema..."
apt-get update -y
apt-get install -y git build-essential cmake python3-pip python3-dev wget curl

# 2. Bibliotecas de aceleração NVIDIA e Quantum
echo "[*] Instalando cuQuantum e Qiskit GPU..."
# Instalamos o qiskit base
pip3 install qiskit --no-cache-dir

# ESSENCIAL: qiskit-aer-gpu traz a compatibilidade com a placa de vídeo
pip3 install qiskit-aer-gpu --no-cache-dir

# cuQuantum é a biblioteca oficial da NVIDIA para aceleração de tensores em GPUs
pip3 install cuquantum cuquantum-python --no-cache-dir

# (O cuBitCrack será executado apenas no PC local do usuário)

echo "=========================================================="
echo "    Setup Concluído! O ambiente está pronto para rodar.   "
echo "=========================================================="
echo "Comando de teste:"
echo "python3 puzzle20_mps_radar.py"
