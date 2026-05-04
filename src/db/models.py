# Rodar este SQL no Supabase (SQL Editor) para criar as tabelas:
#
# -- Dados pessoais do usuário, sem vínculo com canal de comunicação
# CREATE TABLE users (
#     id               BIGSERIAL PRIMARY KEY,
#     name             TEXT NOT NULL,
#     apelido          TEXT,
#     email            TEXT,
#     telefone         TEXT,
#     data_nascimento  TEXT,
#     cpf              TEXT,
#     profissao        TEXT,
#     monthly_income   NUMERIC(10, 2),
#     tg_username      TEXT,
#     tg_idioma        TEXT,
#     tg_premium       BOOLEAN DEFAULT FALSE,
#     created_at       TIMESTAMPTZ DEFAULT NOW()
# );
#
# -- Vincula um usuário a um canal (telegram, whatsapp, etc.)
# CREATE TABLE user_channels (
#     id               BIGSERIAL PRIMARY KEY,
#     user_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
#     channel          TEXT NOT NULL,        -- ex: 'telegram', 'whatsapp'
#     channel_user_id  TEXT NOT NULL,        -- ID do usuário no canal
#     created_at       TIMESTAMPTZ DEFAULT NOW(),
#     UNIQUE (channel, channel_user_id)      -- evita duplicatas por canal
# );
#
# -- Gastos fixos mensais (aluguel, academia, etc.)
# CREATE TABLE fixed_expenses (
#     id          BIGSERIAL PRIMARY KEY,
#     user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
#     description TEXT NOT NULL,
#     amount      NUMERIC(10, 2) NOT NULL,
#     due_day     SMALLINT,                  -- dia do vencimento (1-31)
#     category    TEXT,
#     created_at  TIMESTAMPTZ DEFAULT NOW()
# );
#
# -- Transações livres registradas pelo usuário
# CREATE TABLE transactions (
#     id          BIGSERIAL PRIMARY KEY,
#     user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
#     description TEXT NOT NULL,
#     amount      NUMERIC(10, 2) NOT NULL,
#     category    TEXT,
#     date        DATE DEFAULT CURRENT_DATE,
#     created_at  TIMESTAMPTZ DEFAULT NOW()
# );
