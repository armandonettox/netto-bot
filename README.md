# netto-bot

Bot de assistente pessoal no Telegram com foco em controle financeiro. Recebe mensagens em linguagem natural, categoriza gastos com IA e fornece dicas personalizadas.

## Como funciona

O usuario conversa com o bot pelo Telegram como se estivesse mandando mensagem para um amigo. O bot interpreta o texto, identifica a intencao (registrar gasto, ver resumo, cadastrar gasto fixo etc.) e executa a acao correspondente.

### Fluxo de cadastro

Na primeira mensagem, o bot detecta que o usuario nao existe no banco e inicia um fluxo de cadastro em etapas: coleta nome, apelido, e-mail, telefone, CPF, profissao e renda mensal. O CPF e encriptado com Fernet antes de ser salvo no banco. Apos o cadastro, o canal do Telegram (chat_id) e vinculado ao usuario.

### Registro de gastos livres

O usuario manda uma mensagem como "gastei 50 reais no mercado" ou "almoco 35 no credito". O Gemini interpreta o texto, extrai o valor, descricao e metodo de pagamento, e sugere uma categoria. O usuario confirma ou corrige antes de salvar.

### Gastos fixos

Mensagens como "tenho aluguel de 1200 todo dia 5" ou "plano de saude 300 vence dia 10" sao detectadas como gastos fixos. O bot extrai valor, descricao e dia de vencimento e salva na tabela `fixed_expenses`. O comando `/gastos_fixos` lista todos com o total mensal.

### Resumo financeiro

O usuario pode pedir "resumo do mes", "quanto gastei essa semana", "gastos de ontem" ou uma data especifica. O Gemini interpreta o periodo, o bot busca as transacoes no banco e monta um resumo por categoria. Ao final, o Gemini gera dicas financeiras personalizadas com base no perfil e nos gastos do periodo.

### Categorizacao com IA

O Gemini 2.5 Flash e usado para:
- Detectar a intencao da mensagem (gasto livre, gasto fixo, resumo, listagem)
- Categorizar o gasto automaticamente (alimentacao, transporte, saude etc.)
- Gerar dicas financeiras personalizadas apos o resumo

## Stack

- **Bot:** Python + python-telegram-bot
- **IA:** Google Gemini API — modelo `gemini-2.5-flash`
- **Banco:** Supabase (PostgreSQL, free tier)
- **Deploy:** Oracle Cloud Always Free — VM Ampere A1 (1 OCPU, 6 GB RAM), Sao Paulo

## Banco de dados

Quatro tabelas no Supabase:

- `users` — dados do usuario (nome, renda, CPF encriptado etc.)
- `user_channels` — vinculo entre chat_id do Telegram e usuario
- `fixed_expenses` — gastos fixos mensais com dia de vencimento
- `transactions` — todas as transacoes livres com valor, categoria e metodo de pagamento

SQL completo de criacao em [src/db/create_tables.sql](src/db/create_tables.sql).

## Estrutura do codigo

```
src/
  bot/
    handlers.py     # roteamento de mensagens e todos os fluxos de conversa
    categories.py   # lista de categorias de gastos usada pelo Gemini
  db/
    database.py     # conexao Supabase (singleton)
    models.py       # documentacao das tabelas
    create_tables.sql
  ai/
    advisor.py      # chamadas ao Gemini: categorizar, detectar intencao, gerar dicas
  utils/
    crypto.py       # encriptacao e decriptacao Fernet para dados sensiveis
main.py             # entry point — inicia o polling do Telegram
Dockerfile          # imagem para deploy na Oracle Cloud
docker-compose.yml  # sobe o container com as variaveis de ambiente
```

## Variaveis de ambiente

Copie `.env.example`, renomeie para `.env` e preencha:

| Variavel | Descricao |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do bot (BotFather) |
| `GEMINI_API_KEY` | Chave da Google AI Studio |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon publica do Supabase |
| `ENCRYPTION_KEY` | Chave Fernet para encriptacao de dados sensiveis |

## Como rodar localmente

```powershell
cd C:\Users\armando.netto\armandonettox\projects\netto-bot
venv\Scripts\activate
python main.py
```

Obs: nao rode localmente enquanto o container estiver rodando na Oracle — dois processos com o mesmo token do Telegram se interferem.

## Como atualizar o deploy

```powershell
# Envia os arquivos atualizados para a VM
scp -i "C:\Users\armando.netto\Downloads\ssh-key-2026-05-16.key" -r src main.py requirements.txt Dockerfile opc@163.176.255.189:/home/opc/netto-bot/

# Rebuilda e reinicia o container
ssh -i "C:\Users\armando.netto\Downloads\ssh-key-2026-05-16.key" opc@163.176.255.189 "cd /home/opc/netto-bot && docker stop netto-bot; docker rm netto-bot; docker build -t netto-bot . && docker run -d --name netto-bot --restart unless-stopped --env-file .env netto-bot"
```

## Observacoes sobre o Gemini API

- Usar obrigatoriamente o modelo `gemini-2.5-flash`
- Os modelos `gemini-2.0-flash` e `gemini-2.0-flash-lite` retornam `limit: 0` no Brasil (free tier bloqueado por regiao)
- Cota do free tier: ~500 requests/dia no `gemini-2.5-flash`

## Status

Fase 1 (controle financeiro) concluida e rodando em producao na Oracle Cloud.
