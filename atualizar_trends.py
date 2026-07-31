import csv
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEEDS = {
    "BR": "https://trends.google.com.br/trending/rss?geo=BR",
    "US": "https://trends.google.com/trending/rss?geo=US"
}

ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

def formatar_volume_br(volume_str):
    """Converte números do RSS (ex: 1,000,000+ ou 500,000+) no padrão visual do Google Trends BR"""
    if not volume_str:
        return "100+"
    clean = volume_str.replace(',', '').replace('+', '').strip()
    try:
        num = int(clean)
        if num >= 1_000_000:
            return f"{num // 1_000_000} mi+"
        elif num >= 1_000:
            return f"{num // 1_000} mil+"
        else:
            return f"{num}+"
    except ValueError:
        return volume_str

def raspar_trends(url, pais):
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
            title_node = item.find('title')
            title = title_node.text.strip() if title_node is not None else ""
            
            approx_traffic = item.find('ht:approx_traffic', namespaces)
            raw_volume = approx_traffic.text.strip() if approx_traffic is not None else "100+"
            
            
            if pais == "BR":
                volume_formatado = formatar_volume_br(raw_volume)
            else:
                volume_formatado = raw_volume

            if title:
                dados.append([title, volume_formatado])
            
        return dados
    except Exception as e:
        print(f"❌ Erro ao raspar {url}: {e}")
        return []

def salvar_csv(dados, caminho_arquivo):
    if not dados:
        print(f" Nenhum dado baixado para {caminho_arquivo}")
        return
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow(["Tendências", "Volume de pesquisa"])
        writer.writerows(dados)
    print(f" Arquivo {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f" Rodando raspagem automática: {datetime.now()}")
    for pais, url in FEEDS.items():
        dados = raspar_trends(url, pais)
        salvar_csv(dados, ARQUIVOS_DESTINO[pais])
