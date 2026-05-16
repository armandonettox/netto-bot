import json
import os
from google import genai
from google.genai import types

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
        "4. GASTO_LIVRE — usuario registrou um gasto pontual (nao recorrente).\n"
        "   Exemplos: 'gastei 50 no mercado', 'acabei de gastar 100 numa padaria no debito',\n"
        "   'comprei uma prancha por mil reais no credito', 'paguei 35 de almoco'\n"
        "   Extraia o valor numerico (converta por extenso: 'mil' = 1000, 'duzentos' = 200 etc.),\n"
        "   uma descricao curta do gasto, e o metodo de pagamento se mencionado.\n"
        '   Metodos validos: "credito", "debito", "pix", "dinheiro", "cheque_especial". Use null se nao mencionado.\n'
        '   Retorne: {"intent": "gasto_livre", "descricao": "<texto>", "valor": <numero float>, "metodo": "<metodo ou null>"}\n\n'
        '5. Para qualquer outra intencao, retorne: {"intent": "desconhecido"}\n\n'
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

    if intent == "gasto_livre":
        descricao = resultado.get("descricao", "").strip()
        valor = resultado.get("valor")
        if not descricao or not valor:
            return {"intent": "desconhecido"}
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return {"intent": "desconhecido"}
        metodo = resultado.get("metodo") or None
        return {"intent": "gasto_livre", "descricao": descricao, "valor": valor, "metodo": metodo}

    return {"intent": "desconhecido"}


async def extract_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict | None:
    """Extrai valor e descricao de uma imagem de nota fiscal ou cupom.

    Retorna {"valor": float, "descricao": str} ou None se nao encontrar.
    """
    prompt = (
        "Voce e um assistente financeiro. Analise esta imagem de nota fiscal ou cupom fiscal.\n"
        "Extraia o valor total pago e uma descricao curta do estabelecimento ou tipo de compra.\n"
        "Responda APENAS com um JSON valido, sem markdown, sem explicacao.\n"
        'Formato: {"valor": <numero float>, "descricao": "<texto curto>"}\n'
        "Se nao for possivel identificar o valor, responda: null"
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        texto = response.text.strip()
        if texto.lower() == "null":
            return None
        resultado = json.loads(texto)
        valor = float(resultado["valor"])
        descricao = str(resultado["descricao"]).strip()
        if not descricao or valor <= 0:
            return None
        return {"valor": valor, "descricao": descricao}
    except Exception:
        return None


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str | None:
    """Transcreve uma mensagem de voz e retorna o texto.

    Retorna o texto transcrito ou None em caso de falha.
    """
    prompt = (
        "Transcreva exatamente o que esta sendo dito neste audio em portugues brasileiro.\n"
        "Responda apenas com o texto transcrito, sem pontuacao extra, sem explicacao."
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        texto = response.text.strip()
        return texto if texto else None
    except Exception:
        return None


async def transcribe_and_detect_intent(audio_bytes: bytes, mime_type: str = "audio/ogg") -> dict:
    """Transcreve audio e detecta intencao em uma unica chamada Gemini.

    Retorna dict com 'transcricao' (str) e os campos do detect_intent,
    ou {"intent": "desconhecido", "transcricao": None} em caso de falha.
    """
    intencoes_exemplo = (
        '{"transcricao": "Gastei 50 no mercado", "intent": "gasto_livre", "descricao": "mercado", "valor": 50.0, "metodo": null}\n'
        '{"transcricao": "Gastei dez reais em dinheiro com agua de coco", "intent": "gasto_livre", "descricao": "agua de coco", "valor": 10.0, "metodo": "dinheiro"}\n'
        '{"transcricao": "Quanto gastei esse mes", "intent": "resumo", "periodo": "mes_atual"}\n'
        '{"transcricao": "Quais sao meus gastos fixos", "intent": "listar_fixos"}\n'
        '{"transcricao": "Tenho aluguel de 1200 todo dia 5", "intent": "cadastrar_fixo", "descricao": "aluguel", "valor": 1200.0, "dia_vencimento": 5}'
    )
    prompt = (
        "Voce e um assistente financeiro. Analise este audio em portugues brasileiro.\n"
        "Faca duas coisas em uma resposta:\n"
        "1. Transcreva exatamente o que foi dito\n"
        "2. Classifique a intencao conforme as regras abaixo\n\n"
        "Intencoes possiveis: resumo, cadastrar_fixo, listar_fixos, gasto_livre, desconhecido\n"
        "Para gasto_livre: extraia descricao, valor (converta por extenso: 'dez' = 10, 'mil' = 1000) e metodo de pagamento.\n"
        'Metodos validos: "credito", "debito", "pix", "dinheiro", "cheque_especial" ou null.\n'
        "Para resumo: inclua periodo (mes_atual, semana_atual, hoje, ontem, data_especifica).\n"
        "Para cadastrar_fixo: inclua descricao, valor e dia_vencimento (1-31 ou null).\n\n"
        "Responda APENAS com um JSON valido, sem markdown. Inclua sempre o campo 'transcricao'.\n"
        "Exemplos:\n"
        f"{intencoes_exemplo}\n\n"
        "JSON:"
    )
    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        resultado = json.loads(response.text.strip())
        transcricao = resultado.get("transcricao", "").strip()
        intent = resultado.get("intent", "desconhecido")

        if intent == "gasto_livre":
            descricao = resultado.get("descricao", "").strip()
            valor = resultado.get("valor")
            if not descricao or not valor:
                return {"intent": "desconhecido", "transcricao": transcricao}
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                return {"intent": "desconhecido", "transcricao": transcricao}
            metodo = resultado.get("metodo") or None
            return {"intent": "gasto_livre", "descricao": descricao, "valor": valor, "metodo": metodo, "transcricao": transcricao}

        if intent == "resumo":
            periodo = resultado.get("periodo")
            if periodo not in _PERIODOS_VALIDOS:
                return {"intent": "desconhecido", "transcricao": transcricao}
            saida: dict = {"intent": "resumo", "periodo": periodo, "transcricao": transcricao}
            if periodo == "data_especifica":
                saida["data"] = resultado.get("data", "")
            return saida

        if intent == "cadastrar_fixo":
            descricao = resultado.get("descricao", "").strip()
            valor = resultado.get("valor")
            if not descricao or not valor:
                return {"intent": "desconhecido", "transcricao": transcricao}
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                return {"intent": "desconhecido", "transcricao": transcricao}
            dia = resultado.get("dia_vencimento")
            if dia is not None:
                try:
                    dia = int(dia)
                    if not 1 <= dia <= 31:
                        dia = None
                except (TypeError, ValueError):
                    dia = None
            return {"intent": "cadastrar_fixo", "descricao": descricao, "valor": valor, "dia_vencimento": dia, "transcricao": transcricao}

        if intent == "listar_fixos":
            return {"intent": "listar_fixos", "transcricao": transcricao}

        return {"intent": "desconhecido", "transcricao": transcricao}
    except Exception:
        return {"intent": "desconhecido", "transcricao": None}


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
