# whatsapp-bot

Bot para WhatsApp com foco inicial em controle financeiro pessoal.

## Objetivo

Receber mensagens de gastos pelo WhatsApp, categorizar automaticamente com IA e fornecer dicas para melhorar o controle financeiro.

## Funcionalidades planejadas

- Registro de renda e gastos fixos
- Categorização automática de gastos via IA
- Resumos e relatórios financeiros
- Dicas personalizadas de controle financeiro

## Stack

- **WhatsApp:** Meta Cloud API (gratuito)
- **Backend:** Python + FastAPI
- **IA:** Google Gemini API (gratuito)
- **Banco de dados:** Supabase (PostgreSQL gratuito)
- **Deploy:** Koyeb (free tier)

## Setup

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload
```
