# Kompetenzatlas Tirol 2.0

Project Repository für StAG-Projekt.

## Preparation

```sh
# Setup Neo4J in Docker
docker run -d --name local_neo4j -e NEO4J_AUTH=neo4j/password123 -p 7474:7474 -p 7687:7687 neo4j:latest

# Setup virtual Environment
python -m virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Check Graph

```SQL
MATCH (a:Company)-[r:HAS_COMPETENCE]->(c:Competence) RETURN a, r, c;
MATCH (a:Company)-[x:PARTNER_OF]->(b:Company) RETURN a, x, b;
```

## Tasks

### Media

* Personas, die das System benutzen und deren Fragen (Prompts)?
* User Interface für das neue System?
* Welche Outlets könnten wir scouten?

### Management

* Crawler bauen
* Meinen Code weiterentwickeln