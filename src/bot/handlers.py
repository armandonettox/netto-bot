import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from src.db.database import get_db
from src.utils.crypto import encrypt
from src.ai.advisor import categorize

METODOS_PAGAMENTO = ["Credito", "Debito", "Pix", "Dinheiro", "Cheque especial"]

_GASTO_RE = re.compile(
    r"(?:gastei|paguei|comprei|gastou|pagou)\s+(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)

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

            # vincula o canal telegram ao usuário
            db.table("user_channels").insert({
                "user_id": user_id,
                "channel": "telegram",
                "channel_user_id": telegram_id,
            }).execute()

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

    if etapa == "aguardando_metodo":
        metodo = text.strip()
        if metodo not in METODOS_PAGAMENTO:
            teclado = ReplyKeyboardMarkup(
                [METODOS_PAGAMENTO[:3], METODOS_PAGAMENTO[3:]],
                one_time_keyboard=True,
                resize_keyboard=True,
            )
            await update.message.reply_text("Escolha um dos metodos listados:", reply_markup=teclado)
            return

        db = get_db()
        db.table("transactions").insert({
            "user_id": user_id,
            "description": context.user_data["gasto_descricao"],
            "amount": context.user_data["gasto_valor"],
            "category": context.user_data["gasto_categoria"],
            "payment_method": metodo.lower().replace(" ", "_"),
        }).execute()

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
        categoria = await categorize(text)

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

    await update.message.reply_text(
        f"Oi, {apelido}! Para registrar um gasto, me manda algo como:\n_Gastei 50 no mercado_",
        parse_mode="Markdown",
    )
