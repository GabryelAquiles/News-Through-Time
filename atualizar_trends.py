import csv
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# Feeds do Google Trends
FEEDS = {
    "BR": "https://trends.google.com.br/trending/rss?geo=BR",
    "US": "https://trends.google.com/trending/rss?geo=US"
}

# Nomes exatos dos seus arquivos CSV no GitHub
ARQUIVOS_DESTINO = {
    "BR": "trending_BR_7d_20260714-0053.csv",
    "US": "trending_US_7d_20260714-0105.csv"
}

def raspar_trends(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        dados = []
        namespaces = {'ht': 'https://trends.google.com/trending/rss'}
        
        for item in root.findall('.//item'):
            title = item.find('title').text
            approx_traffic = item.find('ht:approx_traffic', namespaces)
            volume = approx_traffic.text if approx_traffic is not None else "0+"
            dados.append([title, volume])
            
        return dados
    except Exception as e:
        print(f"Erro ao raspar {url}: {e}")
        return []

def salvar_csv(dados, caminho_arquivo):
    if not dados:
        print(f" Nenhum dado baixado para {caminho_arquivo}")
        return
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Termo", "Volume_Texto"])
        writer.writerows(dados)
    print(f" Arquivo {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f" Rodando raspagem automática: {datetime.now()}")
    for pais, url in FEEDS.items():
        dados = raspar_trends(url)
        salvar_csv(dados, ARQUIVOS_DESTINO[pais])
