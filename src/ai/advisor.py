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
    response = await _get_client().aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    categoria = response.text.strip().lower()
    if categoria not in CATEGORIES:
        return "outros"
    return categoria


async def get_financial_tip(summary: dict) -> str:
    # TODO: gerar dica financeira baseada no resumo do usuário
    pass
