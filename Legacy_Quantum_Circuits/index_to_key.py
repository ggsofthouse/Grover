# index_to_key.py
import hashlib

# Tabela do Base58 (sem 0, O, I, l)
B58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def base58_encode(b: bytes) -> str:
    """Codifica bytes puros para formato Base58 do Bitcoin."""
    # Conta os zeros iniciais para manter o padding
    zeros = 0
    for byte in b:
        if byte == 0:
            zeros += 1
        else:
            break
            
    # Converte os bytes para um número inteiro gigante
    n = int.from_bytes(b, 'big')
    
    # Faz a divisão sucessiva por 58
    result = ''
    while n > 0:
        n, mod = divmod(n, 58)
        result = B58_ALPHABET[mod] + result
        
    # Adiciona o caractere '1' para cada byte 0x00 inicial
    return (B58_ALPHABET[0] * zeros) + result

def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def generate_wif(privkey_hex: str, compressed: bool = True) -> str:
    """
    Gera o WIF (Wallet Import Format) a partir de uma chave privada em Hex.
    """
    # 1. Garante que a chave tenha exatos 64 caracteres (256 bits)
    privkey_hex = privkey_hex.zfill(64)
    privkey_bytes = bytes.fromhex(privkey_hex)
    
    # 2. Adiciona o byte da Mainnet (0x80) na frente
    extended_key = b'\x80' + privkey_bytes
    
    # 3. Se for comprimida (padrão dos puzzles modernos), adiciona 0x01 no final
    if compressed:
        extended_key += b'\x01'
        
    # 4. Duplo SHA-256 para gerar o Checksum
    checksum = sha256(sha256(extended_key))[:4]
    
    # 5. Concatena tudo (Chave Estendida + Checksum de 4 bytes)
    final_key = extended_key + checksum
    
    # 6. Codifica para Base58
    return base58_encode(final_key)

def grover_to_bitcoin_keys(range_start_hex: str, grover_offset_decimal: int):
    """
    Traduz a saída quântica (o offset da janela) para chaves clássicas do Bitcoin.
    """
    start_int = int(range_start_hex, 16)
    
    # O Pulo do Gato Clássico: Soma a base do Range com o Offset Colapsado pelo Grover
    absolute_key_int = start_int + grover_offset_decimal
    
    # Formata como Hexadecimal de 256 bits (64 caracteres) preenchido com Zeros
    absolute_key_hex = f"{absolute_key_int:064x}"
    
    print("==========================================================")
    print("   [ PASSO 1 ] TRADUTOR QUÂNTICO -> CLÁSSICO (WIF)")
    print("==========================================================")
    print(f"Base do Range de Busca : 0x{range_start_hex}")
    print(f"Offset colapsado (QPU) : + {grover_offset_decimal}")
    print("----------------------------------------------------------")
    print(f"Chave Privada (Hex)    : {absolute_key_hex}")
    
    # Gera o WIF para importar na carteira (Ex: Electrum)
    wif_compressed = generate_wif(absolute_key_hex, compressed=True)
    wif_uncompressed = generate_wif(absolute_key_hex, compressed=False)
    
    print(f"WIF (Comprimido)       : {wif_compressed}")
    print(f"WIF (Não-comprimido)   : {wif_uncompressed}")
    print("==========================================================")
    print("Pronto para saque na Electrum/Sparrow!")
    
    return absolute_key_hex, wif_compressed

if __name__ == "__main__":
    # Teste de Mesa com o Alvo Real que validamos antes (Puzzle 20)
    # Range começava em 80000 e o colapso na janela (4 bits) foi 10
    grover_to_bitcoin_keys(range_start_hex="80000", grover_offset_decimal=10)
