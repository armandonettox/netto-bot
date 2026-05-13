# netto-bot

Bot de assistente pessoal no Telegram com foco em controle financeiro.

## Objetivo

Receber mensagens de gastos pelo Telegram, categorizar automaticamente com IA e fornecer dicas personalizadas para melhorar o controle financeiro.

## Funcionalidades

- [x] Cadastro de usuario (nome, apelido, e-mail, telefone, CPF, profissao, renda)
- [x] Encriptacao de dados sensiveis (CPF)
- [x] Vinculo de canal Telegram ao usuario
- [x] Registro de gastos livres ("Gastei 50 no mercado")
- [x] Categorizacao automatica via Gemini 2.5 Flash
- [x] Selecao de metodo de pagamento (credito, debito, pix, dinheiro, cheque especial)
- [ ] Registro de gastos fixos
- [ ] Resumo mensal (`/resumo`)
- [ ] Dicas financeiras personalizadas
- [ ] Deploy no Koyeb

## Stack

- **Bot:** Python + python-telegram-bot
- **IA:** Google Gemini API — modelo `gemini-2.5-flash`
- **Banco:** Supabase (PostgreSQL, free tier)
- **Deploy:** Koyeb (free tier, sem sleep) — pendente

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

## Observacoes sobre o Gemini API

- Usar obrigatoriamente o modelo `gemini-2.5-flash`
- Os modelos `gemini-2.0-flash` e `gemini-2.0-flash-lite` retornam `limit: 0` no Brasil (free tier bloqueado por regiao)
- Chaves criadas no Google AI Studio com conta pessoal Gmail funcionam normalmente com `gemini-2.5-flash`
- Cota do free tier: ~500 requests/dia no `gemini-2.5-flash`

## Estrutura

```
src/
  bot/
    handlers.py     # fluxo de cadastro, registro de gastos e roteamento
    categories.py   # categorias de gastos
  db/
    database.py     # conexao Supabase (singleton)
    models.py       # documentacao das tabelas
    create_tables.sql  # SQL de criacao das tabelas
  ai/
    advisor.py      # Gemini: categorizar gastos e gerar dicas
  utils/
    crypto.py       # encriptacao/decriptacao com Fernet
main.py             # entry point — polling Telegram
Dockerfile          # para deploy no Koyeb
```

## Banco de dados

Tabelas: `users`, `user_channels`, `fixed_expenses`, `transactions`

SQL completo de criacao em [src/db/create_tables.sql](src/db/create_tables.sql).

## Proximos passos

- [ ] Comando `/resumo` — visao do mes (total gasto, por categoria, saldo)
- [ ] Registro de gastos fixos com vencimento
- [ ] Dicas financeiras personalizadas via Gemini
- [ ] Tratamento de erros amigavel para o usuario (mensagens no bot em vez de silencio)
- [ ] Deploy no Koyeb para rodar 24h

## Status

Em desenvolvimento — fase 1 (controle financeiro basico) em andamento.
