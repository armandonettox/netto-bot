# netto-bot

Bot de assistente pessoal no Telegram. Foco inicial em controle financeiro — registrar renda, gastos fixos e transações livres, categorizar com IA e dar dicas personalizadas.

## Stack

- **Bot:** Python + python-telegram-bot
- **IA:** Google Gemini API (free tier)
- **Banco:** Supabase (PostgreSQL, free tier)
- **Deploy:** Oracle Cloud Always Free — VM Ampere A1 (1 OCPU, 6 GB RAM), IP: 163.176.255.189

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

1. Primeiro acesso → cadastro em etapas (nome, apelido, email, telefone, CPF, profissao, renda)
2. Usuario cadastrado → Gemini detecta intencao da mensagem e roteia para o handler correto
3. Gastos livres → Gemini categoriza, usuario confirma, salva em `transactions`
4. Gastos fixos → Gemini extrai valor e vencimento, salva em `fixed_expenses`
5. Resumo → busca transacoes por periodo, monta resumo por categoria, Gemini gera dicas

## Deploy

- VM Oracle Cloud: `163.176.255.189` (usuario: `opc`)
- Chave SSH: `C:\Users\armando.netto\Downloads\ssh-key-2026-05-16.key`
- Container rodando com `--restart unless-stopped`
- Servico systemd `netto-bot` configurado para subir com a VM

## Commits

Formato: `tipo(escopo): descrição em português`
Tipos: feat, fix, docs, chore, refactor, test
