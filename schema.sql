CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    cash NUMERIC NOT NULL DEFAULT 10000.00
);

CREATE TABLE sqlite_sequence(name,seq);

CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    symbol TEXT NOT NULL,
    share_price NUMERIC NOT NULL,
    share_quantity INTEGER NOT NULL,
    total_paid NUMERIC NOT NULL,
    type TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX idx_user_id ON transactions (user_id);
CREATE INDEX idx_symbol ON transactions (symbol);

CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    share_quantity INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX idx_portfolio_user_id ON portfolio (user_id);
CREATE INDEX idx_portfolio_symbol ON portfolio (symbol);
