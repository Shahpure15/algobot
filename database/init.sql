-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- User API credentials table
CREATE TABLE IF NOT EXISTS user_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    api_key VARCHAR(128) NOT NULL,
    api_secret VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    UNIQUE(user_id, provider)
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity NUMERIC(16,8) NOT NULL,
    price NUMERIC(16,8) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    delta_order_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS connection_status (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    is_connected BOOLEAN DEFAULT FALSE,
    last_check TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a partial index to handle uniqueness with NULL user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_connection_status_unique 
ON connection_status (provider, COALESCE(user_id, -1));

-- Insert initial connection status for system-wide connections
INSERT INTO connection_status (provider, is_connected, user_id) 
VALUES ('delta_exchange', FALSE, NULL) 
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_user_credentials_user_id ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credentials_provider ON user_credentials(provider);

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_delta_order_id ON trades(delta_order_id);

CREATE INDEX IF NOT EXISTS idx_connection_status_user_id ON connection_status(user_id);
CREATE INDEX IF NOT EXISTS idx_connection_status_provider ON connection_status(provider);