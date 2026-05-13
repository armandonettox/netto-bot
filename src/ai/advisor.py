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

    Retorna um dict com intent e campos extras dependendo da intencao:

    resumo:
      - periodo: "mes_atual" | "semana_atual" | "hoje" | "ontem" | "data_especifica"
      - data: "YYYY-MM-DD" (so quando periodo = data_especifica)

    cadastrar_fixo:
      - descricao: nome do gasto (ex: "aluguel")
      - valor: numero float (ex: 1200.0)
      - dia_vencimento: inteiro 1-31 ou null se nao informado

    listar_fixos: sem campos extras
    """
    prompt = (
        "Voce e um classificador de intencao para um bot financeiro pessoal.\n"
        "Analise a mensagem abaixo e responda APENAS com um JSON valido, sem markdown, sem explicacao.\n\n"
        "Intencoes possiveis:\n\n"
        "1. RESUMO — usuario quer ver o que gastou em algum periodo.\n"
        "   Exemplos: 'quanto gastei esse mes', 'resumo de hoje', 'o que gastei ontem', 'relatorio da semana', 'me mostra meus gastos'\n"
        '   Retorne: {"intent": "resumo", "periodo": "<periodo>"}\n'
        '   Periodos validos: "mes_atual", "semana_atual", "hoje", "ontem", "data_especifica"\n'
        '   Se for data_especifica, inclua "data" no formato YYYY-MM-DD.\n\n'
        "2. CADASTRAR_FIXO — usuario quer registrar um gasto fixo recorrente.\n"
        "   Exemplos: 'tenho aluguel de 1200 todo dia 5', 'pago academia 100 reais todo mes dia 10',\n"
        "   'adiciona netflix 45 reais', 'todo dia 15 pago 200 de conta de luz', 'seguro do carro 300 por mes',\n"
        "   'cadastra meu plano de saude 350 vencimento dia 20', 'tenho uma conta fixa de internet 120',\n"
        "   'minha fatura do cartao vence dia 10 e e em torno de 800'\n"
        '   Retorne: {"intent": "cadastrar_fixo", "descricao": "<nome>", "valor": <numero>, "dia_vencimento": <1-31 ou null>}\n\n'
        "3. LISTAR_FIXOS — usuario quer ver seus gastos fixos cadastrados.\n"
        "   Exemplos: 'quais sao meus gastos fixos', 'me mostra meus fixos', 'lista meus gastos mensais',\n"
        "   'quanto tenho de fixo todo mes', 'quais contas fixas tenho', 'meus compromissos mensais',\n"
        "   'o que pago todo mes', 'meus debitos mensais'\n"
        '   Retorne: {"intent": "listar_fixos"}\n\n'
        '4. Para qualquer outra intencao, retorne: {"intent": "desconhecido"}\n\n'
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

    intent = resultado.get("intent")

    if intent == "resumo":
        periodo = resultado.get("periodo")
        if periodo not in _PERIODOS_VALIDOS:
            return {"intent": "desconhecido"}
        saida: dict = {"intent": "resumo", "periodo": periodo}
        if periodo == "data_especifica":
            saida["data"] = resultado.get("data", "")
        return saida

    if intent == "cadastrar_fixo":
        descricao = resultado.get("descricao", "").strip()
        valor = resultado.get("valor")
        if not descricao or not valor:
            return {"intent": "desconhecido"}
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return {"intent": "desconhecido"}
        dia = resultado.get("dia_vencimento")
        if dia is not None:
            try:
                dia = int(dia)
                if not 1 <= dia <= 31:
                    dia = None
            except (TypeError, ValueError):
                dia = None
        return {"intent": "cadastrar_fixo", "descricao": descricao, "valor": valor, "dia_vencimento": dia}

    if intent == "listar_fixos":
        return {"intent": "listar_fixos"}

    return {"intent": "desconhecido"}


async def get_financial_tip(summary: dict) -> str:
    """Gera uma dica financeira personalizada com base no resumo do usuario.

    summary deve conter:
      - total: float — total gasto no periodo
      - renda: float — renda mensal (0 se nao disponivel)
      - categorias: dict[str, float] — gastos por categoria
      - periodo: str — descricao do periodo (ex: "Maio/2026")
    """
    categorias_texto = "\n".join(
        f"  - {cat}: R$ {valor:,.2f}" for cat, valor in summary["categorias"].items()
    )
    renda = summary.get("renda", 0)
    renda_texto = f"Renda mensal: R$ {renda:,.2f}" if renda else "Renda mensal: nao informada"

    prompt = (
        "Voce e um assistente financeiro pessoal brasileiro, direto e amigavel.\n"
        "Com base no resumo de gastos abaixo, gere UMA dica financeira curta e pratica.\n\n"
        "Regras:\n"
        "- Maximo 3 linhas\n"
        "- Tom amigavel, sem julgamentos\n"
        "- Foco na categoria com maior gasto ou no saldo disponivel\n"
        "- Nao repita os numeros do resumo, so use-os para embasar a dica\n"
        "- Responda apenas a dica, sem titulo, sem introducao\n"
        "- Nao use emojis\n\n"
        f"Periodo: {summary['periodo']}\n"
        f"{renda_texto}\n"
        f"Total gasto: R$ {summary['total']:,.2f}\n"
        f"Por categoria:\n{categorias_texto}\n"
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return ""
