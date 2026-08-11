import sys
from qiskit_ibm_runtime import QiskitRuntimeService

def main():
    if len(sys.argv) < 2:
        print("Uso: python fetch_ibm_result.py <JOB_ID>")
        print("Exemplo: python fetch_ibm_result.py d9t7gn1dsedc73aiitsg")
        return
        
    job_id = sys.argv[1]
    print(f"[*] Buscando resultados do Job: {job_id} na nuvem da IBM...")
    
    try:
        service = QiskitRuntimeService(channel='ibm_quantum_platform')
        job = service.job(job_id)
    except Exception as e:
        print(f"[!] Erro ao conectar na IBM: {e}")
        return
    
    status = job.status()
    print(f"Status atual do Job: {status}")
    
    if str(status).upper() not in ["DONE", "JOB_STATUS_DONE"]:
        print("\nO Job ainda não terminou de rodar no hardware físico.")
        print("Aguarde mais um pouco e tente novamente.")
        return
        
    print("\n[+] Job finalizado! Extraindo o colapso quântico do ruído...")
    job_result = job.result()
    
    # No SamplerV2, acessamos os dados através do nome do Registrador Clássico (meas_key)
    try:
        pub_result = job_result[0].data.meas_key.get_counts()
    except AttributeError:
        print("[!] Erro: Não foi possível encontrar o registrador 'meas_key' nos resultados.")
        return
    
    # Ordenar do mais provável para o menos provável
    sorted_counts = sorted(pub_result.items(), key=lambda x: x[1], reverse=True)
    
    print("\n==========================================================")
    print("   RESULTADO FÍSICO (IBM MARRAKESH)")
    print("==========================================================")
    print("Top 5 estados quânticos que sobreviveram à Decoerência:\n")
    
    total_shots = sum(pub_result.values())
    
    for i, (state, shots) in enumerate(sorted_counts[:5]):
        confianca = (shots / total_shots) * 100
        marcador = " <--- ALVO DO PUZZLE" if state == "10" else ""
        print(f" {i+1}º Lugar: Binário [{state}] | Tiros: {shots} | Confiança: {confianca:.2f}% {marcador}")
        
    print("\n==========================================================")
    if sorted_counts[0][0] == "10":
        print("[VITÓRIA ABSOLUTA] O sinal quântico venceu o ruído do universo!")
    else:
        print("[FÍSICA IMPLACÁVEL] A decoerência venceu. O hardware atual não segurou a coerência.")

if __name__ == "__main__":
    main()
