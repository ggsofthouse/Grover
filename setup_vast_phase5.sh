#!/bin/bash
# =====================================================================
# SCRIPT DE DEPLOY VAST.AI - FASE 5 (ALGEBRAIC TENSOR CRYPTANALYSIS)
# =====================================================================
# Este script prepara uma máquina Ubuntu zerada na Vast.ai para rodar
# o pipeline de Extração de Chave Pública via Redes Tensoriais e SAT.

set -e

echo "[*] Atualizando repositórios locais..."
sudo apt-get update -y

echo "[*] Instalando dependências do sistema e Python3..."
sudo apt-get install -y git python3-pip python3-dev build-essential

echo "[*] Baixando a biblioteca criptográfica do projeto (Grover)..."
if [ -d "Grover" ]; then
    echo "    -> Repositório Grover já existe. Puxando atualizações..."
    cd Grover
    git pull
else
    echo "    -> Clonando repositório principal..."
    git clone https://github.com/ggsofthouse/Grover.git
    cd Grover
fi

echo "[*] Instalando pacotes matemáticos e de física estatística (TensorNetwork, PySAT, Base58)..."
# Usamos o pip3 com flag --break-system-packages caso o Ubuntu (23+) reclame do ambiente global
pip3 install base58 python-sat tensornetwork numpy pycryptodome --break-system-packages || pip3 install base58 python-sat tensornetwork numpy pycryptodome

echo "[*] Ambiente Fase 5 Configurado com Sucesso!"
echo ""
echo "====================================================================="
echo "   COMO EXECUTAR O PIPELINE TENSORIAL:"
echo "====================================================================="
echo "1. Entre no diretório da Fase 5:"
echo "   cd Algebraic_Tensor_Cryptanalysis"
echo ""
echo "2. Gere as equações lógicas do Hash160 (Puzzle 20):"
echo "   python3 1_sat_generator_real.py"
echo ""
echo "3. Transforme a lógica em tensores multidimensionais:"
echo "   python3 2_tensor_mapper.py"
echo ""
echo "4. Rode o otimizador (DMRG) para extrair a Chave Pública Exata:"
echo "   python3 3_exact_preimage_finder.py"
echo "====================================================================="
