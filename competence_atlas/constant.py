from os import getenv

# Models in Use
LANG_MODEL = "llama3.1:latest"
EMBED_MODEL = "qwen3-embedding:0.6b"

# Model Parameters
CONTEXT_SIZE = 8192
EXTRACT_TEMPERATURE = 0
INFERENCE_TEMPERATUR = 0.2
SYSTEM_PROMPT = """Extrahiere aus dem Text Firmenname, Kompetenzen
(kurze Fachbegriffe) und genannte Partnerfirmen. Erfinde nichts,
was nicht im Text steht."""

# NEO4J Schema
SCHEMA_COMPANY = "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE"
SCHEMA_COMPETENCE = "CREATE CONSTRAINT comp_name IF NOT EXISTS FOR (k:Competence) REQUIRE k.name IS UNIQUE"

# NEO4J ACCESS
USER = "neo4j"
PASSWORD = getenv("NEO4J_PASSWORD")