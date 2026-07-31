import csv
import json
import urllib.request
from datetime import datetime

# URLs da API de Tendências Diárias Consolidadas do Google Trends
URLS = {
    "BR": "https://trends.google.com.br/trends/api/dailytrends?hl=pt-BR&tz=180&geo=BR",
    "US": "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=300&geo=US"
}

# Nomes padronizados dos arquivos CSV que o seu script.js lê
ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

def obter_tendencias_consolidadas(url, pais):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            raw_text = response.read().decode('utf-8')
            
        # O Google inclui ')]}\'\n' no início do JSON por motivos de segurança; removemos essa linha
        cleaned_text = raw_text.replace(")]}'\n", "").strip()
        data = json.loads(cleaned_text)
        
        dados = []
        days = data.get("default", {}).get("trendingSearchesDays", [])
        
        for day in days:
            searches = day.get("trendingSearches", [])
            for item in searches:
                termo = item.get("title", {}).get("query", "")
                formatted_traffic = item.get("formattedTraffic", "100+")
                
                if termo:
                    dados.append([termo, formatted_traffic])
                    
        return dados
    except Exception as e:
        print(f" Erro ao buscar dados de {pais}: {e}")
        return []

def salvar_csv(dados, caminho_arquivo):
    if not dados:
        print(f" Nenhum dado retornado para {caminho_arquivo}")
        return
    
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Tendências", "Volume de pesquisa"])
        writer.writerows(dados)
        
    print(f" Arquivo {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f" [BOT] Iniciando raspagem de tendências consolidadas: {datetime.now()}")
    for pais, url in URLS.items():
        dados = obter_tendencias_consolidadas(url, pais)
        salvar_csv(dados, ARQUIVOS_DESTINO[pais])
