
-- PharmaStock database

CREATE TABLE pharmacy (
    pharmacy_id INTEGER PRIMARY KEY,
    pharmacy_name VARCHAR(150) NOT NULL,
    pharmacy_country VARCHAR(100) NOT NULL
);

CREATE TABLE pharma (
    pharma_id INTEGER PRIMARY KEY,
    pharma_name VARCHAR(200) NOT NULL,
    pharma_country VARCHAR(100),
    pharma_market_value NUMERIC(14,2),
    pharma_origin_year INTEGER CHECK (pharma_origin_year BETWEEN 1800 AND 2100)
);

CREATE TABLE ingredient (
    ingredient_id INTEGER PRIMARY KEY,
    ingredient_name VARCHAR(200) NOT NULL,
    ingredient_value NUMERIC(10,2),
    ingredient_type VARCHAR(80)
);

CREATE TABLE illness (
    illness_id INTEGER PRIMARY KEY,
    illness_name VARCHAR(200) NOT NULL,
    illness_type VARCHAR(100),
    illness_danger_level VARCHAR(20)
        CHECK (illness_danger_level IN ('low', 'moderate', 'high')),
    illness_pre_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE med (
    med_id INTEGER PRIMARY KEY,
    med_name VARCHAR(250) NOT NULL,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    illness_id INTEGER REFERENCES illness(illness_id),
    type VARCHAR(100),
    form VARCHAR(80),
    pharma_id INTEGER REFERENCES pharma(pharma_id),
    dosage_strength VARCHAR(100),
    expiry_date DATE,
    prescription_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE med_ingredient (
    med_id INTEGER REFERENCES med(med_id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredient(ingredient_id),
    PRIMARY KEY (med_id, ingredient_id)
);

CREATE TABLE med_illness (
    med_id INTEGER REFERENCES med(med_id) ON DELETE CASCADE,
    illness_id INTEGER REFERENCES illness(illness_id),
    PRIMARY KEY (med_id, illness_id)
);

CREATE TABLE dosage (
    dosage_id INTEGER PRIMARY KEY,
    med_id INTEGER NOT NULL REFERENCES med(med_id) ON DELETE CASCADE,
    age_group VARCHAR(30) NOT NULL
        CHECK (age_group IN ('adult', 'child')),
    dosage_note VARCHAR(120),
    times_per_day INTEGER CHECK (times_per_day BETWEEN 1 AND 10)
);

CREATE TABLE stock (
    stock_id INTEGER PRIMARY KEY,
    pharmacy_id INTEGER NOT NULL REFERENCES pharmacy(pharmacy_id),
    med_id INTEGER NOT NULL REFERENCES med(med_id) ON DELETE CASCADE,
    stock_type VARCHAR(20) NOT NULL CHECK (stock_type IN ('web', 'local')),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    expiry_date DATE,
    unit_price NUMERIC(10,2) CHECK (unit_price >= 0),
    UNIQUE (pharmacy_id, med_id, stock_type)
);

CREATE TABLE import_batch (
    import_batch_id INTEGER PRIMARY KEY,
    source_name VARCHAR(200) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    import_date DATE NOT NULL,
    notes TEXT
);

CREATE INDEX idx_med_name ON med (med_name);
CREATE INDEX idx_med_type ON med (type);
CREATE INDEX idx_med_form ON med (form);
CREATE INDEX idx_med_pharma ON med (pharma_id);
CREATE INDEX idx_illness_name ON illness (illness_name);
CREATE INDEX idx_ingredient_name ON ingredient (ingredient_name);
CREATE INDEX idx_stock_pharmacy ON stock (pharmacy_id, stock_type);

-- Web Stock membership (the Kaggle dataset will set this to TRUE)
ALTER TABLE med ADD COLUMN IF NOT EXISTS in_web BOOLEAN NOT NULL DEFAULT FALSE;

-- Activity log shown in the website's History panel
CREATE TABLE IF NOT EXISTS history (
    history_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pharmacy_id INTEGER REFERENCES pharmacy(pharmacy_id) ON DELETE CASCADE,
    stock_type VARCHAR(20) NOT NULL CHECK (stock_type IN ('web', 'local')),
    action VARCHAR(20) NOT NULL
        CHECK (action IN ('seed', 'import', 'download', 'add', 'edit', 'delete')),
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_history_pharmacy ON history (pharmacy_id, stock_type, created_at DESC);
