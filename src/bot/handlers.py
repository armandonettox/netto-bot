import re
from datetime import date, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from src.db.database import get_db
from src.utils.crypto import encrypt
from src.ai.advisor import categorize, detect_intent

METODOS_PAGAMENTO = ["Credito", "Debito", "Pix", "Dinheiro", "Cheque especial"]

_SINONIMOS_METODO = {
    "credito": "Credito",
    "crédito": "Credito",
    "cartao": "Credito",
    "cartão": "Credito",
    "cartao de credito": "Credito",
    "cartão de crédito": "Credito",
    "debito": "Debito",
    "débito": "Debito",
    "cartao de debito": "Debito",
    "cartão de débito": "Debito",
    "pix": "Pix",
    "dinheiro": "Dinheiro",
    "especie": "Dinheiro",
    "espécie": "Dinheiro",
    "cheque especial": "Cheque especial",
    "cheque": "Cheque especial",
}

_GASTO_RE = re.compile(
    r"(?:gastei|paguei|comprei|gastou|pagou)\s+(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)

_MSG_ERRO = "Ops, algo deu errado por aqui. Tenta de novo em alguns instantes."


async def _erro(update: Update, mensagem: str = _MSG_ERRO) -> None:
    await update.message.reply_text(mensagem)


APRESENTACAO = (
    "Ola! Eu sou o *Netto*, seu assistente pessoal.\n\n"
    "Posso te ajudar com:\n"
    "• Controle financeiro — registre gastos e renda\n"
    "• Resumos mensais — veja para onde seu dinheiro vai\n"
    "• Dicas personalizadas — melhore suas financas\n"
    "• E muito mais em breve!\n\n"
    "Vamos comecar com um cadastro rapido."
)


def _nome_completo_telegram(user) -> str:
    partes = [user.first_name or "", user.last_name or ""]
    return " ".join(p for p in partes if p).strip()


def _validar_nome_completo(nome: str) -> str | None:
    """Retorna mensagem de erro ou None se valido."""
    if re.search(r"\d", nome):
        return "O nome nao pode conter numeros. Tenta de novo."
    palavras = [p for p in nome.split() if len(p) >= 2]
    if len(palavras) < 2:
        return "Por favor, informe seu nome e sobrenome completos."
    if not re.match(r"^[A-Za-zÀ-ÿ\s]+$", nome):
        return "O nome so pode conter letras. Tenta de novo."
    return None


def _validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email))


def _validar_telefone(telefone: str) -> bool:
    t = re.sub(r"\D", "", telefone)
    if len(t) not in (10, 11):
        return False
    # celular com 11 digitos deve ter 9 como primeiro digito apos o DDD
    if len(t) == 11 and t[2] != "9":
        return False
    return True


def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True


def _validar_data(data: str) -> bool:
    return bool(re.match(r"^\d{2}/\d{2}/\d{4}$", data.strip()))


def _eh_confirmacao(text: str) -> bool:
    return text.lower() in ("sim", "s", "confirma", "confirmado", "pode", "isso", "yes", "ok")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    telegram_id = str(tg_user.id)
    text = update.message.text.strip()

    db = get_db()
    # busca o usuário pelo canal telegram na tabela user_channels
    canal = db.table("user_channels").select("user_id").eq("channel", "telegram").eq("channel_user_id", telegram_id).execute()
    if canal.data:
        user_id = canal.data[0]["user_id"]
        resultado = db.table("users").select("id, name, monthly_income").eq("id", user_id).execute()
        usuario = resultado.data[0] if resultado.data else None
    else:
        usuario = None

    if usuario is None:
        estado = context.user_data.get("cadastro_etapa")

        # --- Apresentacao ---
        if estado is None:
            context.user_data["tg_nome"] = _nome_completo_telegram(tg_user)
            context.user_data["tg_username"] = tg_user.username or ""
            context.user_data["tg_idioma"] = tg_user.language_code or ""
            context.user_data["tg_premium"] = tg_user.is_premium or False

            nome_sugerido = context.user_data["tg_nome"]
            if nome_sugerido:
                await update.message.reply_text(
                    f"Ola, *{nome_sugerido}*! Eu sou o *Netto*, seu assistente pessoal.\n\n"
                    "Posso te ajudar com:\n"
                    "• Controle financeiro — registre gastos e renda\n"
                    "• Resumos mensais — veja para onde seu dinheiro vai\n"
                    "• Dicas personalizadas — melhore suas financas\n"
                    "• E muito mais em breve!\n\n"
                    "Vamos comecar com um cadastro rapido.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(APRESENTACAO, parse_mode="Markdown")

            context.user_data["cadastro_etapa"] = "aguardando_nome_completo"
            await update.message.reply_text("Qual e o seu nome completo?")
            return

        # --- Nome completo ---
        if estado == "aguardando_nome_completo":
            erro = _validar_nome_completo(text)
            if erro:
                await update.message.reply_text(erro)
                return
            context.user_data["nome_completo"] = text
            context.user_data["cadastro_etapa"] = "aguardando_apelido"

            tg_nome = context.user_data["tg_nome"]
            if tg_nome:
                await update.message.reply_text(
                    f"Prefere ser chamado de *{tg_nome}* (seu apelido no Telegram) ou prefere outro apelido?",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("Como prefere ser chamado? (apelido)")
            return

        # --- Apelido ---
        if estado == "aguardando_apelido":
            tg_nome = context.user_data["tg_nome"]
            if tg_nome and _eh_confirmacao(text):
                apelido = tg_nome
            else:
                apelido = text
            context.user_data["apelido"] = apelido
            context.user_data["cadastro_etapa"] = "aguardando_email"
            await update.message.reply_text(f"Combinado, *{apelido}*! Qual e o seu e-mail?", parse_mode="Markdown")
            return

        # --- E-mail ---
        if estado == "aguardando_email":
            if not _validar_email(text):
                await update.message.reply_text("Nao parece um e-mail valido. Tenta de novo, ex: *nome@email.com*", parse_mode="Markdown")
                return
            context.user_data["email"] = text.lower()
            context.user_data["cadastro_etapa"] = "aguardando_telefone"
            await update.message.reply_text("Qual e o seu celular com DDD? (ex: 11999999999)")
            return

        # --- Telefone ---
        if estado == "aguardando_telefone":
            if not _validar_telefone(text):
                await update.message.reply_text("Numero invalido. Manda o celular com DDD, ex: *11999999999*", parse_mode="Markdown")
                return
            context.user_data["telefone"] = re.sub(r"\D", "", text)
            context.user_data["cadastro_etapa"] = "aguardando_nascimento"
            await update.message.reply_text("Qual e a sua data de nascimento? (ex: 25/03/1999)")
            return

        # --- Data de nascimento ---
        if estado == "aguardando_nascimento":
            if not _validar_data(text):
                await update.message.reply_text("Formato invalido. Use *DD/MM/AAAA*, ex: 25/03/1999", parse_mode="Markdown")
                return
            context.user_data["nascimento"] = text.strip()
            context.user_data["cadastro_etapa"] = "aguardando_cpf"
            await update.message.reply_text("Qual e o seu CPF? (so os numeros ou com pontuacao)")
            return

        # --- CPF ---
        if estado == "aguardando_cpf":
            if not _validar_cpf(text):
                await update.message.reply_text("CPF invalido. Verifica e tenta de novo.")
                return
            cpf_limpo = re.sub(r"\D", "", text)
            context.user_data["cpf"] = encrypt(cpf_limpo)
            context.user_data["cadastro_etapa"] = "aguardando_profissao"
            await update.message.reply_text("Qual e a sua profissao?")
            return

        # --- Profissao ---
        if estado == "aguardando_profissao":
            if not text or len(text) < 2:
                await update.message.reply_text("Por favor, informe sua profissao.")
                return
            context.user_data["profissao"] = text
            context.user_data["cadastro_etapa"] = "aguardando_renda"
            await update.message.reply_text("Otimo! Ultimo passo: qual e a sua renda mensal? (ex: 3500)")
            return

        # --- Renda ---
        if estado == "aguardando_renda":
            try:
                renda = float(text.replace(",", ".").replace("R$", "").strip())
            except ValueError:
                await update.message.reply_text("Nao entendi o valor. Manda so o numero, ex: *3500*", parse_mode="Markdown")
                return

            apelido = context.user_data["apelido"]

            # insere o usuário e recupera o id gerado
            try:
                resultado_insert = db.table("users").insert({
                    "name": context.user_data["nome_completo"],
                    "apelido": apelido,
                    "email": context.user_data["email"],
                    "telefone": context.user_data["telefone"],
                    "data_nascimento": context.user_data["nascimento"],
                    "cpf": context.user_data["cpf"],
                    "profissao": context.user_data["profissao"],
                    "monthly_income": renda,
                    "tg_username": context.user_data["tg_username"],
                    "tg_idioma": context.user_data["tg_idioma"],
                    "tg_premium": context.user_data["tg_premium"],
                }).execute()
                user_id = resultado_insert.data[0]["id"]
                db.table("user_channels").insert({
                    "user_id": user_id,
                    "channel": "telegram",
                    "channel_user_id": telegram_id,
                }).execute()
            except Exception:
                await _erro(update, "Nao consegui salvar seu cadastro. Tenta de novo em alguns instantes.")
                return

            context.user_data.clear()

            await update.message.reply_text(
                f"Cadastro feito, {apelido}!\n\n"
                f"Renda registrada: *R$ {renda:,.2f}*\n\n"
                "Agora e so me mandar seus gastos no formato:\n"
                "_Gastei 50 no mercado_\n"
                "_Paguei 80 de gasolina_",
                parse_mode="Markdown"
            )
            return

    # Usuario ja cadastrado — fluxo de registro de gasto
    apelido = usuario.get("apelido") or usuario["name"].split()[0]
    etapa = context.user_data.get("gasto_etapa")
    fixo_etapa = context.user_data.get("fixo_etapa")

    if fixo_etapa == "aguardando_confirmacao":
        if _eh_confirmacao(text):
            descricao = context.user_data["fixo_descricao"]
            valor = context.user_data["fixo_valor"]
            dia = context.user_data["fixo_dia"]
            context.user_data.clear()
            categoria = await categorize(descricao)
            try:
                db = get_db()
                db.table("fixed_expenses").insert({
                    "user_id": user_id,
                    "description": descricao,
                    "amount": valor,
                    "due_day": dia,
                    "category": categoria,
                }).execute()
            except Exception:
                await _erro(update, "Nao consegui salvar o gasto fixo. Tenta de novo em alguns instantes.")
                return
            dia_texto = f"todo dia *{dia}*" if dia else "sem data de vencimento"
            await update.message.reply_text(
                f"Gasto fixo cadastrado!\n\n"
                f"Nome: *{descricao.capitalize()}*\n"
                f"Valor: *R$ {valor:,.2f}*\n"
                f"Vencimento: {dia_texto}\n"
                f"Categoria: {categoria}",
                parse_mode="Markdown",
            )
        else:
            context.user_data.clear()
            await update.message.reply_text("Tudo bem, nao salvei nada.")
        return

    if etapa == "aguardando_metodo":
        metodo_digitado = text.strip().lower()
        metodo = _SINONIMOS_METODO.get(metodo_digitado)
        if metodo is None:
            teclado = ReplyKeyboardMarkup(
                [METODOS_PAGAMENTO[:3], METODOS_PAGAMENTO[3:]],
                one_time_keyboard=True,
                resize_keyboard=True,
            )
            await update.message.reply_text("Nao reconheci esse metodo. Escolha um da lista:", reply_markup=teclado)
            return

        try:
            db = get_db()
            db.table("transactions").insert({
                "user_id": user_id,
                "description": context.user_data["gasto_descricao"],
                "amount": context.user_data["gasto_valor"],
                "category": context.user_data["gasto_categoria"],
                "payment_method": metodo.lower().replace(" ", "_"),
            }).execute()
        except Exception:
            await _erro(update, "Nao consegui salvar o gasto. Tenta de novo em alguns instantes.")
            context.user_data.clear()
            return

        valor = context.user_data["gasto_valor"]
        categoria = context.user_data["gasto_categoria"]
        context.user_data.clear()

        await update.message.reply_text(
            f"Gasto registrado!\n\n"
            f"Valor: *R$ {valor:,.2f}*\n"
            f"Categoria: {categoria}\n"
            f"Pagamento: {metodo}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    match = _GASTO_RE.search(text)
    if match:
        valor_str = match.group(1).replace(",", ".")
        valor = float(valor_str)
        try:
            categoria = await categorize(text)
        except Exception:
            categoria = "outros"

        context.user_data["gasto_etapa"] = "aguardando_metodo"
        context.user_data["gasto_descricao"] = text
        context.user_data["gasto_valor"] = valor
        context.user_data["gasto_categoria"] = categoria

        teclado = ReplyKeyboardMarkup(
            [METODOS_PAGAMENTO[:3], METODOS_PAGAMENTO[3:]],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
        await update.message.reply_text(
            f"Entendido! *R$ {valor:,.2f}* em _{categoria}_.\nQual foi o metodo de pagamento?",
            parse_mode="Markdown",
            reply_markup=teclado,
        )
        return

    intencao = await detect_intent(text)

    if intencao["intent"] == "resumo":
        await _enviar_resumo(
            update,
            user_id,
            usuario,
            intencao["periodo"],
            intencao.get("data", ""),
        )
        return

    if intencao["intent"] == "cadastrar_fixo":
        descricao = intencao["descricao"]
        valor = intencao["valor"]
        dia = intencao.get("dia_vencimento")

        context.user_data["fixo_etapa"] = "aguardando_confirmacao"
        context.user_data["fixo_descricao"] = descricao
        context.user_data["fixo_valor"] = valor
        context.user_data["fixo_dia"] = dia

        dia_texto = f"todo dia *{dia}*" if dia else "sem dia de vencimento definido"
        await update.message.reply_text(
            f"Vou cadastrar o seguinte gasto fixo:\n\n"
            f"Nome: *{descricao.capitalize()}*\n"
            f"Valor: *R$ {valor:,.2f}*\n"
            f"Vencimento: {dia_texto}\n\n"
            "Confirma? (sim / nao)",
            parse_mode="Markdown",
        )
        return

    if intencao["intent"] == "listar_fixos":
        await _listar_fixos(update, user_id, apelido)
        return

    await update.message.reply_text(
        f"Oi, {apelido}! Para registrar um gasto, me manda algo como:\n_Gastei 50 no mercado_",
        parse_mode="Markdown",
    )


async def _listar_fixos(update: Update, user_id: str, apelido: str) -> None:
    try:
        db = get_db()
        fixos = (
            db.table("fixed_expenses")
            .select("description, amount, due_day, category")
            .eq("user_id", user_id)
            .order("due_day", desc=False, nullsfirst=False)
            .execute()
            .data
        )
    except Exception:
        await _erro(update)
        return

    if not fixos:
        await update.message.reply_text(
            "Voce ainda nao tem gastos fixos cadastrados.\n\n"
            "Me manda algo como:\n_Tenho aluguel de 1200 todo dia 5_",
            parse_mode="Markdown",
        )
        return

    total = sum(float(f["amount"]) for f in fixos)
    linhas = []
    for f in fixos:
        dia = f"dia {f['due_day']}" if f["due_day"] else "sem vencimento"
        linhas.append(f"  • *{f['description'].capitalize()}* — R$ {float(f['amount']):,.2f} ({dia})")

    mensagem = (
        f"Gastos fixos — {apelido}\n\n"
        + "\n".join(linhas)
        + f"\n\n*Total mensal: R$ {total:,.2f}*"
    )
    await update.message.reply_text(mensagem, parse_mode="Markdown")


_MESES = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _intervalo_periodo(periodo: str, data_especifica: str = "") -> tuple[date, date, str]:
    """Retorna (inicio, fim, titulo) para o periodo solicitado.

    fim sempre recebe +1 dia para compensar fuso UTC do servidor (Koyeb).
    """
    hoje = date.today()
    margem = timedelta(days=1)
    if periodo == "hoje":
        return hoje, hoje + margem, f"Hoje ({hoje.strftime('%d/%m/%Y')})"
    if periodo == "ontem":
        ontem = hoje - timedelta(days=1)
        return ontem, ontem + margem, f"Ontem ({ontem.strftime('%d/%m/%Y')})"
    if periodo == "semana_atual":
        inicio = hoje - timedelta(days=hoje.weekday())
        return inicio, hoje + margem, f"Esta semana ({inicio.strftime('%d/%m')} a {hoje.strftime('%d/%m')})"
    if periodo == "data_especifica" and data_especifica:
        try:
            d = date.fromisoformat(data_especifica)
            return d, d + margem, d.strftime("%d/%m/%Y")
        except ValueError:
            pass
    # padrao: mes_atual
    inicio = hoje.replace(day=1)
    return inicio, hoje + margem, f"{_MESES[hoje.month]}/{hoje.year}"


async def _enviar_resumo(update: Update, user_id: int, usuario: dict, periodo: str, data_especifica: str = "") -> None:
    apelido = usuario.get("apelido") or usuario["name"].split()[0]
    renda = float(usuario["monthly_income"] or 0)

    inicio, fim, titulo = _intervalo_periodo(periodo, data_especifica)

    try:
        db = get_db()
        transacoes = (
            db.table("transactions")
            .select("amount, category")
            .eq("user_id", user_id)
            .gte("date", inicio.isoformat())
            .lte("date", fim.isoformat())
            .execute()
            .data
        )
    except Exception:
        await _erro(update)
        return

    if not transacoes:
        await update.message.reply_text(
            f"Nenhum gasto registrado para o periodo: *{titulo}*.",
            parse_mode="Markdown",
        )
        return

    total = sum(float(t["amount"]) for t in transacoes)
    saldo = renda - total

    por_categoria: dict[str, float] = {}
    for t in transacoes:
        cat = t["category"] or "outros"
        por_categoria[cat] = por_categoria.get(cat, 0) + float(t["amount"])

    linhas_categorias = "\n".join(
        f"  • {cat.capitalize()}: *R$ {valor:,.2f}*"
        for cat, valor in sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)
    )

    saldo_texto = f"*R$ {saldo:,.2f}*" if saldo >= 0 else f"*-R$ {abs(saldo):,.2f}* (no negativo!)"

    # so mostra renda/saldo no resumo do mes (nao faz sentido para dia ou semana)
    if periodo in ("mes_atual",):
        cabecalho = (
            f"Renda mensal: *R$ {renda:,.2f}*\n"
            f"Total gasto: *R$ {total:,.2f}*\n"
            f"Saldo estimado: {saldo_texto}\n\n"
        )
    else:
        cabecalho = f"Total gasto: *R$ {total:,.2f}*\n\n"

    mensagem = (
        f"Resumo — *{titulo}* — {apelido}\n\n"
        f"{cabecalho}"
        f"*Por categoria:*\n{linhas_categorias}"
    )

    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def resumo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    telegram_id = str(tg_user.id)

    db = get_db()
    canal = db.table("user_channels").select("user_id").eq("channel", "telegram").eq("channel_user_id", telegram_id).execute()

    if not canal.data:
        await update.message.reply_text("Voce ainda nao tem cadastro. Me manda uma mensagem para comecarmos!")
        return

    user_id = canal.data[0]["user_id"]
    try:
        resultado = db.table("users").select("apelido, name, monthly_income").eq("id", user_id).execute()
        if not resultado.data:
            await _erro(update, "Nao encontrei seus dados. Tenta de novo em alguns instantes.")
            return
        usuario = resultado.data[0]
    except Exception:
        await _erro(update)
        return
    await _enviar_resumo(update, user_id, usuario, "mes_atual")
