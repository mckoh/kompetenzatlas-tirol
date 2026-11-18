from os import getenv

# Models in Use
LANG_MODEL = "llama3.1:latest"
EMBED_MODEL = "qwen3-embedding:0.6b"

# Model Parameters
CONTEXT_SIZE = 8192
EXTRACT_TEMPERATURE = 0
INFERENCE_TEMPERATUR = 0.2
EXTRACTION_PROMPT_A = """Extrahiere aus dem Text Firmenname, Kompetenzen
(kurze Fachbegriffe) und genannte Partnerfirmen. Erfinde nichts,
was nicht im Text steht."""
EXTRACTION_PROMPT_B = """Extrahiere aus dem Text Firmenname und Kompetenzen
(kurze Fachbegriffe). Erfinde nichts, was nicht im Text steht."""

# NEO4J Schema
SCHEMA_COMPANY = "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE"
SCHEMA_COMPETENCE = "CREATE CONSTRAINT comp_name IF NOT EXISTS FOR (k:Competence) REQUIRE k.name IS UNIQUE"

# NEO4J ACCESS
USER = "neo4j"
PASSWORD = getenv("NEO4J_PASSWORD")

# European Patent Service
AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/rest-services/published-data/search"