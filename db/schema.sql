PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS debts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lender_name TEXT NOT NULL,
    debt_type TEXT NOT NULL,
    original_currency TEXT NOT NULL,
    principal_original REAL NOT NULL,
    principal_outstanding_cad REAL NOT NULL,
    interest_rate_annual REAL NOT NULL,
    penal_rate_annual REAL NOT NULL,
    loan_start_date TEXT NOT NULL,
    installment_amount REAL,
    installment_due_day INTEGER,
    last_payment_date TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS credit_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL,
    card_name TEXT NOT NULL,
    credit_limit_cad REAL NOT NULL,
    statement_balance_cad REAL NOT NULL,
    interest_rate_annual REAL NOT NULL,
    statement_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    last_payment_date TEXT,
    flat_late_fee_cad REAL NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_date TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    payment_amount_original REAL NOT NULL,
    payment_currency TEXT NOT NULL,
    payment_amount_cad REAL NOT NULL,
    applied_penal REAL NOT NULL,
    applied_interest REAL NOT NULL,
    applied_principal REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    currency TEXT NOT NULL,
    balance_cad REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_rates (
    currency TEXT PRIMARY KEY,
    rate_to_cad REAL NOT NULL,
    last_updated TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monthly_snapshots (
    snapshot_date TEXT PRIMARY KEY,
    total_debt_cad REAL NOT NULL,
    total_interest_cad REAL NOT NULL,
    total_savings_cad REAL NOT NULL,
    net_position_cad REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payments_target ON payments (target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments (payment_date);
CREATE INDEX IF NOT EXISTS idx_debts_status ON debts (status);
CREATE INDEX IF NOT EXISTS idx_cards_status ON credit_cards (status);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON monthly_snapshots (snapshot_date);
