import csv
import json
import re
import urllib.request
from datetime import datetime

# URLs da API Oficial de Tendências Consolidadas
URLS = {
    "BR": "https://trends.google.com.br/trends/api/dailytrends?hl=pt-BR&tz=180&geo=BR",
    "US": "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=300&geo=US"
}

ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

def limpar_texto(texto):
    """Remove quebras de linha invisíveis que quebram o CSV"""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

def obter_tendencias_consolidadas(url, pais):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            raw_text = response.read().decode('utf-8')
            
        # O Google inclui ')]}\'\n' no início do JSON por segurança
        cleaned_text = raw_text.replace(")]}'\n", "").strip()
        data = json.loads(cleaned_text)
        
        dados = []
        days = data.get("default", {}).get("trendingSearchesDays", [])
        
        for day in days:
            searches = day.get("trendingSearches", [])
            for item in searches:
                termo = limpar_texto(item.get("title", {}).get("query", ""))
                formatted_traffic = limpar_texto(item.get("formattedTraffic", "100+"))
                
                if termo:
                    dados.append([termo, formatted_traffic])
                    
        return dados
    except Exception as e:
        print(f"❌ Erro ao buscar dados de {pais}: {e}")
        return []

def salvar_csv(dados, caminho_arquivo):
    if not dados:
        print(f"⚠️ Nenhum dado retornado para {caminho_arquivo}")
        return
    
    # Salva com quebra de linha limpa e codificação UTF-8
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Tendências", "Volume de pesquisa"])
        writer.writerows(dados)
        
    print(f"✅ Arquivo {caminho_arquivo} gerado com sucesso e sem erros de formatação!")

if __name__ == "__main__":
    print(f"🚀 [BOT] Atualizando dados no GitHub: {datetime.now()}")
    for pais, url in URLS.items():
        dados = obter_tendencias_consolidadas(url, pais)
        salvar_csv(dados, ARQUIVOS_DESTINO[pais])
