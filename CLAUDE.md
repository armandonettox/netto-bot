# netto-bot

Bot de assistente pessoal no Telegram. Foco inicial em controle financeiro — registrar renda, gastos fixos e transações livres, categorizar com IA e dar dicas personalizadas.

## Stack

- **Bot:** Python + python-telegram-bot
- **IA:** Google Gemini API (free tier)
- **Banco:** Supabase (PostgreSQL, free tier)
- **Deploy:** Koyeb (free tier, sem sleep)

## Rodar localmente

```powershell
cd C:\Users\armando.netto\armandonettox\projects\netto-bot
venv\Scripts\activate
python main.py
```

Requer `.env` preenchido (ver `.env.example`).

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do @mynetto_bot (BotFather) |
| `GEMINI_API_KEY` | Chave da Google AI Studio |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon pública do Supabase |

## Estrutura

```
src/
  bot/
    handlers.py     # roteamento de mensagens e fluxo de cadastro
    categories.py   # lista de categorias de gastos
  db/
    database.py     # conexão Supabase (singleton)
    models.py       # documentação das tabelas
  ai/
    advisor.py      # Gemini: categorizar gastos e gerar dicas
main.py             # entry point — polling Telegram
Dockerfile          # para deploy no Koyeb
```

## Banco de dados (Supabase)

Tabelas: `users`, `fixed_expenses`, `transactions`

Script de criação em `src/db/models.py` (comentários com o SQL completo).

## Fluxo atual

1. Primeiro acesso → bot se apresenta e coleta nome + renda mensal
2. Usuário cadastrado → ecoa mensagem (próximo: categorizar gastos)

## Próximos passos

- [ ] Criar tabelas no Supabase (rodar SQL do models.py)
- [ ] Implementar registro de gastos livres ("Gastei 50 no mercado")
- [ ] Integrar Gemini para categorização automática
- [ ] Implementar `/resumo` — visão do mês
- [ ] Implementar registro de gastos fixos
- [ ] Dicas financeiras via Gemini
- [ ] Deploy no Koyeb

## Commits

Formato: `tipo(escopo): descrição em português`
Tipos: feat, fix, docs, chore, refactor, test
