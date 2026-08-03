import os
import json
import csv
import urllib.request
import urllib.parse
from datetime import datetime

# URL da API do Google Trends
URLS = {
    "BR": "https://trends.google.com.br/trends/api/dailytrends?hl=pt-BR&tz=180&geo=BR",
    "US": "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=300&geo=US"
}

ARQUIVOS_DESTINO = {
    "BR": "trending_BR_latest.csv",
    "US": "trending_US_latest.csv"
}

# Pega a chave da API do Gemini configurada nas variáveis de ambiente do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def obter_dados_brutos(url):
    """Baixa o JSON bruto do Google Trends"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            raw_text = response.read().decode('utf-8')
            return raw_text.replace(")]}'\n", "").strip()
    except Exception as e:
        print(f"❌ Erro ao baixar dados da URL {url}: {e}")
        return None

def processar_com_gemini(json_texto, pais):
    """Envia os dados brutos para o Gemini limpar e formatar em CSV de 2 colunas"""
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY não encontrada. Usando processamento local...")
        return processar_localmente(json_texto)

    url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "Você é um assistente de dados. Analise o JSON bruto do Google Trends abaixo e extraia "
        "apenas os termos buscados e seus respectivos volumes de pesquisa.\n"
        "REGRAS ESTRITAS:\n"
        "1. Retorne APENAS um texto no formato CSV válido com exatamente 2 colunas: Tendências,Volume de pesquisa\n"
        "2. Não inclua marcas de bloco de código como ```csv ou ```.\n"
        "3. Remova quebras de linha dentro dos nomes das tendências.\n"
        "4. Mantenha os volumes no formato exato como '100 mil+', '1 mi+', '50 mil+', etc.\n"
        "5. Não adicione nenhuma explicação, introdução ou texto além do próprio CSV.\n\n"
        f"DADOS BRUTOS DO GOOGLE TRENDS ({pais}):\n"
        f"{json_texto[:15000]}" # Limita tamanho para a requisição
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
        print(f"⚠️ Falha na chamada da API Gemini: {e}. Usando fallback local...")
        return processar_localmente(json_texto)

def processar_localmente(json_texto):
    """Fallback simples em Python caso a API do Gemini falhe"""
    try:
        data = json.loads(json_texto)
        linhas = ["Tendências,Volume de pesquisa"]
        days = data.get("default", {}).get("trendingSearchesDays", [])
        for day in days:
            for item in day.get("trendingSearches", []):
                termo = item.get("title", {}).get("query", "").replace("\n", " ").replace(",", " ").strip()
                volume = item.get("formattedTraffic", "100+").replace("\n", " ").strip()
                if termo:
                    linhas.append(f'"{termo}","{volume}"')
        return "\n".join(linhas)
    except Exception as e:
        print(f"❌ Erro no processamento local: {e}")
        return ""

def salvar_csv(conteudo_csv, caminho_arquivo):
    if not conteudo_csv:
        print(f"⚠️ Sem conteúdo para salvar em {caminho_arquivo}")
        return

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo_csv)
    print(f"✅ Ficheiro {caminho_arquivo} atualizado com sucesso!")

if __name__ == "__main__":
    print(f"🚀 [BOT] Iniciando atualização via Gemini em {datetime.now()}")
    
    for pais, url in URLS.items():
        json_bruto = obter_dados_brutos(url)
        if json_bruto:
            csv_limpo = processar_com_gemini(json_bruto, pais)
            salvar_csv(csv_limpo, ARQUIVOS_DESTINO[pais])
