from neo4j import GraphDatabase
from ollama import chat

from .extractor import embed
from .constant import SCHEMA_COMPANY, SCHEMA_COMPETENCE
from .constant import LANG_MODEL, INFERENCE_TEMPERATUR, CONTEXT_SIZE
from .constant import USER, PASSWORD


driver = GraphDatabase.driver("bolt://localhost:7687", auth=(USER, PASSWORD))
DIM = len(embed(["test"])[0])  # Dimension nicht hartcodieren (je nach Modellgröße verschieden)

def init_schema():
    with driver.session() as s:
        s.run(SCHEMA_COMPANY)
        s.run(SCHEMA_COMPETENCE)
        for label, idx in [("Competence", "competence_emb"), ("Chunk", "chunk_emb")]:
            s.run(f"""
              CREATE VECTOR INDEX {idx} IF NOT EXISTS
              FOR (n:{label}) ON (n.embedding)
              OPTIONS {{indexConfig: {{
                `vector.dimensions`: {DIM},
                `vector.similarity_function`: 'cosine'}}}}""")

def store(ex, source_url: str, chunk_text: str):
    comp_vecs = embed(ex.competences) if ex.competences else []
    chunk_vec = embed([chunk_text])[0]
    with driver.session() as session:
        session.run("MERGE (c:Company {name:$n})", n=ex.company_name)
        for name, vec in zip(ex.competences, comp_vecs):
            session.run("""
              MATCH (c:Company {name:$company})
              MERGE (k:Competence {name:$k})
              WITH c, k
              CALL db.create.setNodeVectorProperty(k, 'embedding', $vec)
              MERGE (c)-[r:HAS_COMPETENCE]->(k)
              SET r.source = $src""",
              company=ex.company_name, k=name, vec=vec, src=source_url)
        for p in ex.partners:
            session.run("""
              MATCH (c:Company {name:$company})
              MERGE (p:Company {name:$p})
              MERGE (c)-[:PARTNER_OF]->(p)""", company=ex.company_name, p=p)
        session.run("""
          MATCH (c:Company {name:$company})
          CREATE (ch:Chunk {text:$t, source_url:$src})
          WITH c, ch
          CALL db.create.setNodeVectorProperty(ch, 'embedding', $vec)
          CREATE (ch)-[:ABOUT]->(c)""",
          company=ex.company_name, t=chunk_text, src=source_url, vec=chunk_vec)

def retrieve(question: str, k: int = 5) -> str:
    qvec = embed([question])[0]
    with driver.session() as session:
        rows = session.run("""
            CYPHER 25
            MATCH (comp:Competence)
            SEARCH comp IN (
                VECTOR INDEX competence_emb
                FOR $q
                LIMIT $k
            ) SCORE AS score
            MATCH (c:Company)-[r:HAS_COMPETENCE]->(comp)
            OPTIONAL MATCH (c)-[:PARTNER_OF]-(p:Company)
            RETURN c.name AS firma, comp.name AS kompetenz, score,
                    r.source AS quelle, collect(DISTINCT p.name) AS partner
            ORDER BY score DESC""", q=qvec, k=k).data()

    companies = []
    for row in rows:
        partner = ", ".join(row['partner']) or '–'
        companies.append(f"- {row['firma']} | Kompetenz: {row['kompetenz']} | Partner: {partner} | Quelle: {row['quelle']}")

    return "\n".join(companies)

def answer(question: str) -> str:
    context = retrieve(question)
    resp = chat(model=LANG_MODEL, messages=[
        {"role": "system", "content":
            "Du bist Berater im Tiroler Kompetenzatlas. Antworte nur anhand des Kontexts, "
            "nenne Firmen und Quellen. Wenn der Kontext nicht reicht, sage das."},
        {"role": "user", "content": f"Kontext:\n{context}\n\nFrage: {question}"},
    ], options={"temperature": INFERENCE_TEMPERATUR, "num_ctx": CONTEXT_SIZE})
    return resp.message.content
