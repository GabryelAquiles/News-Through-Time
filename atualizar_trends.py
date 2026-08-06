import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import math

# Feeds RSS oficiais do Google Trends
URLS = {
    "BR": "https://trends.google.com/trending/rss?geo=BR",
    "US": "https://trends.google.com/trending/rss?geo=US"
}

ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def calcular_tempo_decorrido(pub_date_str):
    """Calcula quanto tempo se passou desde a publicação (ex: 'há 20 minutos', 'há 2 horas')"""
    try:
        # Exemplo de data no RSS: 'Thu, 06 Aug 2026 14:10:00 +0000' ou 'GMT'
        if 'GMT' in pub_date_str:
            pub_date_str = pub_date_str.replace('GMT', '+0000')
            
        data_publicacao = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        agora = datetime.now(timezone.utc)
        
        diferenca_segundos = (agora - data_publicacao).total_seconds()
        
        minutos = math.floor(diferenca_segundos / 60)
        horas = math.floor(minutos / 60)
        dias = math.floor(horas / 24)
        
        if minutos < 1:
            return "agora mesmo"
        elif minutos < 60:
            return f"há {minutos} minuto{'s' if minutos > 1 else ''}"
        elif horas < 24:
            return f"há {horas} hora{'s' if horas > 1 else ''}"
        else:
            return f"há {dias} dia{'s' if dias > 1 else ''}"
    except Exception as e:
        return "recente"

def obter_dados_brutos_rss(url):
    """Baixa o RSS oficial do Google Trends"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f" Erro ao baixar RSS da URL {url}: {e}")
        return None

def processar_com_gemini(xml_texto, pais):
    """Envia o XML para o Gemini formatar em 3 colunas: Tendências, Volume de pesquisa, Tempo"""
    if not GEMINI_API_KEY:
        print(" GEMINI_API_KEY não encontrada. Usando processamento local...")
        return processar_localmente_xml(xml_texto)

    url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "Você é um assistente de dados. Analise o XML RSS do Google Trends abaixo e extraia:\n"
        "1. Título do termo buscado\n"
        "2. Volume estimado de buscas (approx_traffic)\n"
        "3. A data/hora de publicação (pubDate) convertida para tempo decorrido aproximado em português (ex: 'há 20 minutos', 'há 2 horas', 'há 1 dia').\n\n"
        "REGRAS ESTRITAS:\n"
        "1. Retorne APENAS um texto no formato CSV válido com exatamente 3 colunas: Tendências,Volume de pesquisa,Tempo\n"
        "2. Não inclua marcas de bloco de código como ```csv ou ```.\n"
        "3. Remova quebras de linha e vírgulas internas do nome dos termos.\n"
        "4. Não adicione nenhuma explicação ou introdução, apenas o CSV.\n\n"
        f"DADOS BRUTOS RSS ({pais}):\n"
        f"{xml_texto[:15000]}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        req = urllib.request.Request(
            url_gemini,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            csv_result = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return csv_result
    except Exception as e:
        print(f" Falha no Gemini: {e}. Usando fallback local...")
        return processar_localmente_xml(xml_texto)

def processar_localmente_xml(xml_texto):
    """Fallback local em Python calculando a diferença de tempo de publicação"""
    try:
        root = ET.fromstring(xml_texto)
        channel = root.find('channel')
        linhas = ["Tendências,Volume de pesquisa,Tempo"]
        
        ns = {'ht': 'https://trends.google.com/trending/rss'}
        
        for item in channel.findall('item'):
            title = item.find('title')
            traffic = item.find('ht:approx_traffic', ns)
            pub_date = item.find('pubDate')
            
            termo = title.text.replace("\n", " ").replace(",", " ").strip() if title is not None else ""
            vol = traffic.text.replace("\n", " ").strip() if traffic is not None else "100.000+"
            
            tempo_str = "recente"
            if pub_date is not None and pub_date.text:
                tempo_str = calcular_tempo_decorrido(pub_date.text.strip())
            
            if termo:
                linhas.append(f'"{termo}","{vol}","{tempo_str}"')
                
        return "\n".join(linhas)
    except Exception as e:
        print(f"❌ Erro no processamento local de XML: {e}")
        return ""

def salvar_csv(conteudo_csv, caminho_arquivo):
    if not conteudo_csv:
        print(f" Sem conteúdo para salvar em {caminho_arquivo}")
        return

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo_csv)
    print(f" Arquivo {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f" [BOT] Iniciando atualização via RSS + Gemini em {datetime.now()}")
    
    for pais, url in URLS.items():
        xml_bruto = obter_dados_brutos_rss(url)
        if xml_bruto:
            csv_limpo = processar_com_gemini(xml_bruto, pais)
            salvar_csv(csv_limpo, ARQUIVOS_DESTINO[pais])
