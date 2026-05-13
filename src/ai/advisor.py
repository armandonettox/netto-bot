import json
import os
from google import genai

CATEGORIES = [
    "alimentacao",
    "transporte",
    "saude",
    "moradia",
    "lazer",
    "educacao",
    "vestuario",
    "outros",
]

_PERIODOS_VALIDOS = {"mes_atual", "semana_atual", "hoje", "ontem", "data_especifica"}

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


async def categorize(description: str) -> str:
    categorias = ", ".join(CATEGORIES)
    prompt = (
        f"Categorize o seguinte gasto em uma das categorias: {categorias}.\n"
        f"Gasto: {description}\n"
        f"Responda apenas com o nome da categoria, sem mais nada."
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        categoria = response.text.strip().lower()
    except Exception:
        return "outros"
    if categoria not in CATEGORIES:
        return "outros"
    return categoria


async def detect_intent(text: str) -> dict:
    """Classifica a intencao da mensagem do usuario.

    Retorna um dict com:
      - intent: "resumo" | "desconhecido"
      - periodo: "mes_atual" | "semana_atual" | "hoje" | "ontem" | "data_especifica"
      - data: "YYYY-MM-DD"  (so quando periodo = data_especifica)
    """
    prompt = (
        "Voce e um classificador de intencao para um bot financeiro pessoal.\n"
        "Analise a mensagem abaixo e responda APENAS com um JSON valido, sem markdown, sem explicacao.\n\n"
        "Regras:\n"
        '- Se o usuario quer ver um resumo, relatorio ou o que gastou em algum periodo, retorne: {"intent": "resumo", "periodo": "<periodo>"}\n'
        '- Periodos validos: "mes_atual", "semana_atual", "hoje", "ontem", "data_especifica"\n'
        '- Se for data_especifica, inclua o campo "data" no formato YYYY-MM-DD. Assuma que o ano eh o atual se nao informado.\n'
        '- Para qualquer outra intencao, retorne: {"intent": "desconhecido"}\n\n'
        f"Mensagem: {text}\n\n"
        "JSON:"
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        resultado = json.loads(response.text.strip())
    except Exception:
        return {"intent": "desconhecido"}

    if resultado.get("intent") != "resumo":
        return {"intent": "desconhecido"}

    periodo = resultado.get("periodo")
    if periodo not in _PERIODOS_VALIDOS:
        return {"intent": "desconhecido"}

    saida: dict = {"intent": "resumo", "periodo": periodo}
    if periodo == "data_especifica":
        saida["data"] = resultado.get("data", "")
    return saida


async def get_financial_tip(summary: dict) -> str:
    # TODO: gerar dica financeira baseada no resumo do usuário
    pass
