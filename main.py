import os
import requests
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()

# Permite chamadas vindas do seu frontend no GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# A chave é lida com segurança da variável de ambiente do servidor
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6KnZ08xBMrFabdIuwjxo9ss2dVJCtZrfLi7qrLzPDwwtg")
genai.configure(api_key=GEMINI_API_KEY)

def carregar_diretrizes_doc():
    # Se usar Google Docs público, altere o ID abaixo
    DOC_ID = "1WsuCVULLHitpG2Lan5-GBX-1cjvs6KFECIIJV7cjPC0"
    url = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"
    res = requests.get(url)
    return res.text if res.status_code == 200 else ""

@app.get("/analisar/{pais}")
def analisar_tendencias(pais: str):
    # 1. Puxa as tendências atualizadas do seu repositório
    csv_url = f"https://raw.githubusercontent.com/GabryelAquiles/News-Through-Time/main/trending_{pais}_latest.csv"
    df = pd.read_csv(csv_url)
    top10 = df.head(10).to_dict(orient="records")

    # 2. Carrega a base de conhecimento/comportamento social
    contexto_sociologico = carregar_diretrizes_doc()

    # 3. Monta o prompt
    prompt = f"""
    Você é um analista sociológico e de dados.
    Base conceitual de análise:
    {contexto_sociologico}

    Tendências de busca no {pais}:
    {top10}

    Escreva um resumo conciso (3 parágrafos curtos) explicando o contexto geral do que as pessoas estão buscando.
    """

    # 4. Chama a IA
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return {"resumo": response.text}