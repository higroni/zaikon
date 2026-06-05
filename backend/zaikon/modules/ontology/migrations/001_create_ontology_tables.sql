-- Ontology Terms Table
CREATE TABLE IF NOT EXISTS ontology_terms (
    term_id TEXT PRIMARY KEY,
    term_type TEXT NOT NULL,  -- 'actor', 'action', 'object', 'domain'
    canonical TEXT NOT NULL,
    label TEXT NOT NULL,
    confidence REAL DEFAULT 0.75,
    frequency INTEGER DEFAULT 1,  -- How many times seen
    source TEXT DEFAULT 'ner',  -- 'manual', 'ner', 'imported'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term_type, canonical, label)
);

-- Ontology Relationships Table
CREATE TABLE IF NOT EXISTS ontology_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_term_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'broader_than', 'narrower_than', 'related_to'
    target_term_id TEXT NOT NULL,
    confidence REAL DEFAULT 0.80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_term_id) REFERENCES ontology_terms(term_id),
    FOREIGN KEY (target_term_id) REFERENCES ontology_terms(term_id),
    UNIQUE(source_term_id, relationship_type, target_term_id)
);

-- Ontology Domains Table
CREATE TABLE IF NOT EXISTS ontology_domains (
    domain_id TEXT PRIMARY KEY,
    term_id TEXT NOT NULL,
    domain_name TEXT NOT NULL,
    confidence REAL DEFAULT 0.75,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (term_id) REFERENCES ontology_terms(term_id),
    UNIQUE(term_id, domain_name)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ontology_terms_type ON ontology_terms(term_type);
CREATE INDEX IF NOT EXISTS idx_ontology_terms_canonical ON ontology_terms(canonical);
CREATE INDEX IF NOT EXISTS idx_ontology_terms_label ON ontology_terms(label);
CREATE INDEX IF NOT EXISTS idx_ontology_terms_frequency ON ontology_terms(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_ontology_relationships_source ON ontology_relationships(source_term_id);
CREATE INDEX IF NOT EXISTS idx_ontology_domains_term ON ontology_domains(term_id);

-- Made with Bob
