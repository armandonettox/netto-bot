from telegram import Update
from telegram.ext import ContextTypes
from src.db.database import get_db

APRESENTACAO = (
    "Olá! Eu sou o *Netto*, seu assistente pessoal 🤖\n\n"
    "Posso te ajudar com:\n"
    "• 💰 Controle financeiro — registre gastos e renda\n"
    "• 📊 Resumos mensais — veja para onde seu dinheiro vai\n"
    "• 💡 Dicas personalizadas — melhore suas finanças\n"
    "• E muito mais em breve!\n\n"
    "Vamos começar com um cadastro rápido.\n\n"
    "Qual é o seu nome?"
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    text = update.message.text.strip()

    db = get_db()
    resultado = db.table("users").select("id, name, monthly_income").eq("phone", telegram_id).execute()
    usuario = resultado.data[0] if resultado.data else None

    # Fluxo de cadastro
    if usuario is None:
        estado = context.user_data.get("cadastro_etapa")

        if estado is None:
            context.user_data["cadastro_etapa"] = "aguardando_nome"
            await update.message.reply_text(APRESENTACAO, parse_mode="Markdown")
            return

        if estado == "aguardando_nome":
            context.user_data["nome"] = text
            context.user_data["cadastro_etapa"] = "aguardando_renda"
            await update.message.reply_text(f"Prazer, {text}! 😊\n\nQual é a sua renda mensal? (ex: 3500)")
            return

        if estado == "aguardando_renda":
            try:
                renda = float(text.replace(",", ".").replace("R$", "").strip())
            except ValueError:
                await update.message.reply_text("Não entendi o valor. Manda só o número, ex: *3500*", parse_mode="Markdown")
                return

            nome = context.user_data["nome"]
            db.table("users").insert({"phone": telegram_id, "name": nome, "monthly_income": renda}).execute()
            context.user_data.clear()

            await update.message.reply_text(
                f"Cadastro feito, {nome}! ✅\n\n"
                f"Renda registrada: *R$ {renda:,.2f}*\n\n"
                "Agora é só me mandar seus gastos no formato:\n"
                "_Gastei 50 no mercado_\n"
                "_Paguei 80 de gasolina_",
                parse_mode="Markdown"
            )
            return

    # Usuário já cadastrado — por enquanto ecoa a mensagem
    await update.message.reply_text(f"Entendido, {usuario['name']}! Em breve processo isso 👍")
