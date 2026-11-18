from os import getenv
from requests import post, get
from ollama import chat
from pydantic import BaseModel
from os import getenv
from epo_ops import Client
from epo_ops.models import Docdb
from epo_ops.models import Epodoc
from warnings import warn
from .constant import AUTH_URL, SEARCH_URL
from .constant import LANG_MODEL, EXTRACTION_PROMPT_B
from .constant import CONTEXT_SIZE, EXTRACT_TEMPERATURE


class Extraction(BaseModel):
    company_name: str
    competences: list[str]


def get_patents_list(company:str) -> list[tuple]:
    """Retrieves list of patents from the European Patent Office's web service.

    Attributes:
        company (str): The company's name (e.g. Swarovski)

    Returns:
        A list of tuples with (document_number, country, type)
    """

    consumer_key = getenv("EPS_CONSUMER_KEY")
    consumer_secret = getenv("EPS_SECRET_KEY")

    auth_url = AUTH_URL
    auth_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth_data = {"grant_type": "client_credentials"}

    auth_response = post(
        auth_url,
        data=auth_data,
        headers=auth_headers,
        auth=(consumer_key, consumer_secret),
    )

    access_token = auth_response.json()["access_token"]
    search_url = SEARCH_URL
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    params = {"q": f"pa = {company}"}

    response = get(
        search_url,
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        data = response.json()

        publications = (
            data.get("ops:world-patent-data", {})
            .get("ops:biblio-search", {})
            .get("ops:search-result", {})
            .get("ops:publication-reference", [])
        )

        patent_list = []

        for item in publications:
            doc_id = item.get("document-id", {})
            doc_number = doc_id.get("doc-number", {}).get("$")
            country = doc_id.get("country", {}).get("$")
            kind_type = doc_id.get("kind", {}).get("$")

            patent_list.append(
                (doc_number, country, kind_type)
            )

        print(f"Successfully retrieved {len(patent_list)} patents.")
        return patent_list

    raise ConnectionError("Connection to EPS service was not successful.")


def extract_invention_title(bib_data: dict) -> str | None:
    """Robustly extracts the title info from a patent document

    Attributes:
        bib_data: A json object with the bibliographic information.

    Returns:
        Title text of the patent.
    """
    titles = bib_data.get("invention-title", [])

    # Falls es ein einzelnes Dict ist, in Liste umwandeln
    if isinstance(titles, dict):
        titles = [titles]

    title_text = None

    # Bevorzugt englischen Titel suchen, sonst deutschen oder ersten verfügbaren nehmen
    for title in titles:
        if isinstance(title, dict):
            lang = title.get("@lang", "")
            text = title.get("$", "")

            if lang == "en":
                return text  # Direkt zurückgeben, wenn Englisch gefunden
            elif lang == "de" and not title_text:
                title_text = text
            elif not title_text:
                title_text = text

    return title_text


def get_patent_data(doc_num, country, doc_type):
    """Retrieves the complete data of a patent from EPO webservice

    Attributes:
        doc_num: Document number of patent
        country: Issuing country of patent
        doc_type: Type of document

    Returns:
        JSON object with all patent data
    """

    client = Client(
        key=getenv("EPS_CONSUMER_KEY"),
        secret=getenv("EPS_SECRET_KEY"),
        accept_type="json",
    )

    try:

        response = client.published_data(
            reference_type="publication",
            input=Docdb(doc_num, country, doc_type),
            endpoint="biblio",
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Keine Daten gefunden für: {doc_num}")

    except Exception as e:
        print(f"Fehler beim Abrufen von {doc_num}: {e}")

    return False


def get_patent_name(patent_data):
    """Extracts the patent name from a patent data JSON object.

    Attributes:
        patent_data: Complete JSON object with patent data.

    Returns:
        Patent name as string.
    """

    world_data = patent_data.get("ops:world-patent-data", {})
    docs = world_data.get("exchange-documents", {}).get("exchange-document", {})

    if isinstance(docs, list):
        doc = docs[0] if docs else {}
    else:
        doc = docs

    bib_data = doc.get("bibliographic-data", {})
    title = extract_invention_title(bib_data)

    if title:
        return title

    print("EPO-Document contains no usable title.")
    return False


def get_patent_names(patent_list: list[tuple]) -> list[str]:
    """Retrieves patent titles using corrected Epodoc formatting (no dot).

    Attributes:
        patent_list: A list of patents with doc_number, country and doc_type

    Returns:
        List of patent titles.
    """

    patent_titles = []

    for doc_num, country, doc_type in patent_list:
        patent_data = get_patent_data(doc_num,  country, doc_type)
        patent_titles.append(get_patent_name(patent_data))

    print(f"Erfolgreich {len(patent_titles)} von {len(patent_list)} Titeln abgerufen.")
    return patent_titles


def summarize_competences(company: str, patent_titles: list[str]) -> str:
    """Uses a Language Model to convert the list of patent titles into competences.

    Prompts an LLM to analyze the provided patent titles and generate a bulleted
    list of core competencies. The output includes an introductory sentence but
    omits section headers, categorical grouping, and concluding summaries.

    Attributes:
        company: The company name as string
        patent_titles: A list of Patent titles as strings

    Returns:
        Model response as text.

    """
    warn(
        "summarize_competences ist veraltet und wird in einer künftigen Version entfernt.",
        category=DeprecationWarning,
        stacklevel=2
    )

    patents_formatted = "\n- ".join(patent_titles)
    prompt = f"""Fasse die Kompetenzen des Unternehmens {company} mit folgenden Patenten als Bullets zusammen.

    Regeln:
    - Nutze einen Bullet pro Kompetenz.
    - Verwende keine Zwischenüberschriften.
    - Schreibe eine Einleitung: '{company} hat folgende Kompetenzen:'.
    - Liste unter der Einleitung die Kompetenzen auf.
    - Erfinde keine zusätzlichen Kompetenzen; fasse nur das zusammen, was die Patente beschreiben.

    Patente:
    - {patents_formatted}"""

    model_response = chat(model=LANG_MODEL, messages=
        [
            {
                "role": "user",
                "content": f"Fasse die Kompetenzen eines Unternehmens mit folgenden Patenten als Bullets zusammen. Nutze einen Bullet pro Kompetenz. Verwende keine Zwischenüberschriften. Schreibe keinen Einleitungstext. Schreibe keine Zusammenfassung. Liste nur die Kompetenzen auf. Erfinde keine zusätzlichen Kompetenzen. Fasse nur das zusammen, was die Patente beschreiben. Hier sind die Patente: {",".join(patent_titles)}"
            }
        ]
    )
    return model_response.message.content


def extract(text: str) -> Extraction:

    resp = chat(
        model=LANG_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT_B},
            {"role": "user", "content": text},
        ],
        format=Extraction.model_json_schema(),
        options={
            "temperature": EXTRACT_TEMPERATURE,
            "num_ctx": CONTEXT_SIZE
        },
    )
    return Extraction.model_validate_json(resp.message.content)


def get_competences_from_patents(company: str) -> Extraction:
    """Retrievs an extraction of competences from the patents of a company.

    Attributes:
        company: The name of the company

    Returns:
        Extraction of competences
    """

    patent_list = get_patents_list(company=company)
    patent_titles = get_patent_names(patent_list=patent_list)

    patents = "\n- ".join(patent_titles)
    text = f"Die Firma {company} hält folgende Patente: {patents}"

    return extract(text)