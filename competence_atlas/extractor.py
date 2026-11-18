from pydantic import BaseModel
from ollama import chat, embeddings

from .constant import CONTEXT_SIZE
from .constant import EXTRACT_TEMPERATURE, EXTRACTION_PROMPT_A
from .constant import LANG_MODEL, EMBED_MODEL


class Extraction(BaseModel):
    company_name: str
    competences: list[str]
    partners: list[str]

def extract(text: str) -> Extraction:
    resp = chat(
        model=LANG_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT_A},
            {"role": "user", "content": text},
        ],
        format=Extraction.model_json_schema(),
        options={
            "temperature": EXTRACT_TEMPERATURE,
            "num_ctx": CONTEXT_SIZE
        },
    )
    return Extraction.model_validate_json(resp.message.content)

def embed(texts: list[str]) -> list[list[float]]:
    return [embeddings(model=EMBED_MODEL, prompt=text).embedding for text in texts]