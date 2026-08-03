import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# Feeds RSS oficiais e estáveis do Google Trends
URLS = {
    "BR": "https://trends.google.com/trending/rss?geo=BR",
    "US": "https://trends.google.com/trending/rss?geo=US"
}

ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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
        print(f"❌ Erro ao baixar RSS da URL {url}: {e}")
        return None

def processar_com_gemini(xml_texto, pais):
    """Envia o XML do RSS para o Gemini extrair e formatar em CSV de 2 colunas"""
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY não encontrada. Usando processamento local...")
        return processar_localmente_xml(xml_texto)

    url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "Você é um assistente de dados. Analise o XML RSS do Google Trends abaixo e extraia "
        "apenas os títulos das tendências e o volume estimado de buscas (approx_traffic).\n"
        "REGRAS ESTRITAS:\n"
        "1. Retorne APENAS um texto no formato CSV válido com exatamente 2 colunas: Tendências,Volume de pesquisa\n"
        "2. Não inclua marcas de bloco de código como ```csv ou ```.\n"
        "3. Remova quebras de linha e vírgulas internas do nome dos termos.\n"
        "4. Mantenha os volumes no formato original (ex: '100.000+', '1.000.000+').\n"
        "5. Não adicione nenhuma explicação ou introdução, apenas o CSV.\n\n"
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
        print(f"⚠️ Falha no Gemini: {e}. Usando fallback local...")
        return processar_localmente_xml(xml_texto)

def processar_localmente_xml(xml_texto):
    """Fallback local para ler o XML caso o Gemini não responda"""
    try:
        root = ET.fromstring(xml_texto)
        channel = root.find('channel')
        linhas = ["Tendências,Volume de pesquisa"]
        
        # Namespace do Google Trends para pegar o tráfego aproximado
        ns = {'ht': 'https://trends.google.com/trending/rss'}
        
        for item in channel.findall('item'):
            title = item.find('title')
            traffic = item.find('ht:approx_traffic', ns)
            
            termo = title.text.replace("\n", " ").replace(",", " ").strip() if title is not None else ""
            vol = traffic.text.replace("\n", " ").strip() if traffic is not None else "100.000+"
            
            if termo:
                linhas.append(f'"{termo}","{vol}"')
                
        return "\n".join(linhas)
    except Exception as e:
        print(f"❌ Erro no processamento local de XML: {e}")
        return ""

def salvar_csv(conteudo_csv, caminho_arquivo):
    if not conteudo_csv:
        print(f"⚠️ Sem conteúdo para salvar em {caminho_arquivo}")
        return

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo_csv)
    print(f"✅ Arquivo {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f"🚀 [BOT] Iniciando atualização via RSS + Gemini em {datetime.now()}")
    
    for pais, url in URLS.items():
        xml_bruto = obter_dados_brutos_rss(url)
        if xml_bruto:
            csv_limpo = processar_com_gemini(xml_bruto, pais)
            salvar_csv(csv_limpo, ARQUIVOS_DESTINO[pais])
