# netto-bot

Bot de assistente pessoal no Telegram com foco em controle financeiro.

## Objetivo

Receber mensagens de gastos pelo Telegram, categorizar automaticamente com IA e fornecer dicas personalizadas para melhorar o controle financeiro.

## Funcionalidades

- [x] Cadastro de usuario (nome, apelido, e-mail, telefone, CPF, profissao, renda)
- [x] Encriptacao de dados sensiveis (CPF)
- [x] Vinculo de canal Telegram ao usuario
- [ ] Registro de gastos livres ("Gastei 50 no mercado")
- [ ] Categorizacao automatica via Gemini
- [ ] Registro de gastos fixos
- [ ] Resumo mensal (`/resumo`)
- [ ] Dicas financeiras personalizadas

## Stack

- **Bot:** Python + python-telegram-bot
- **IA:** Google Gemini API (free tier)
- **Banco:** Supabase (PostgreSQL, free tier)
- **Deploy:** Koyeb (free tier, sem sleep)

## Como rodar localmente

```powershell
cd C:\Users\armando.netto\armandonettox\projects\netto-bot
venv\Scripts\activate
python main.py
```

Requer `.env` preenchido — copie `.env.example` e preencha as variaveis.

## Variaveis de ambiente

| Variavel | Descricao |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do bot (BotFather) |
| `GEMINI_API_KEY` | Chave da Google AI Studio |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon publica do Supabase |
| `ENCRYPTION_KEY` | Chave Fernet para encriptacao de dados sensiveis |

## Estrutura

```
src/
  bot/
    handlers.py     # fluxo de cadastro e roteamento de mensagens
    categories.py   # categorias de gastos
  db/
    database.py     # conexao Supabase (singleton)
    models.py       # SQL de criacao das tabelas
  ai/
    advisor.py      # Gemini: categorizar gastos e gerar dicas
  utils/
    crypto.py       # encriptacao/decriptacao com Fernet
main.py             # entry point — polling Telegram
Dockerfile          # para deploy no Koyeb
```

## Banco de dados

Tabelas: `users`, `user_channels`, `fixed_expenses`, `transactions`

SQL completo de criacao em [src/db/models.py](src/db/models.py).

## Status

Em desenvolvimento.
