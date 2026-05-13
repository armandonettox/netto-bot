CREATE TABLE users (
    id               BIGSERIAL PRIMARY KEY,
    name             TEXT NOT NULL,
    apelido          TEXT,
    email            TEXT,
    telefone         TEXT,
    data_nascimento  TEXT,
    cpf              TEXT,
    profissao        TEXT,
    monthly_income   NUMERIC(10, 2),
    tg_username      TEXT,
    tg_idioma        TEXT,
    tg_premium       BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_channels (
    id               BIGSERIAL PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel          TEXT NOT NULL,
    channel_user_id  TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (channel, channel_user_id)
);

CREATE TABLE fixed_expenses (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,
    due_day     SMALLINT,
    category    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,
    category    TEXT,
    date        DATE DEFAULT CURRENT_DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
