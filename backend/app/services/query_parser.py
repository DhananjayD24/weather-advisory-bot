import json

from pydantic import BaseModel, Field, ValidationError

from app.services.llm_service import get_llm


class ParsedQuery(BaseModel):
    activity: str | None = Field(
        default=None,
        description="Outdoor activity explicitly mentioned by the user."
    )
    location: str | None = Field(
        default=None,
        description="Location explicitly mentioned by the user."
    )
    time_context: str | None = Field(
        default=None,
        description="Requested time such as today, tomorrow, this evening."
    )
    user_type: str | None = Field(
        default=None,
        description="Relevant user type explicitly mentioned by the user."
    )


PARSER_PROMPT = """
You are the query-understanding component of a weather safety chatbot.

Extract ONLY information explicitly stated or clearly requested in the
user's message.

Return ONLY valid JSON with exactly these four fields:

{
  "activity": null,
  "location": null,
  "time_context": null,
  "user_type": null
}

Rules:
- Do not invent missing information.
- Do not give safety advice.
- Do not answer the user's question.
- Do not infer a location from unrelated information.
- If a field is not present, use null.
- Preserve the user's intended time meaning.
- Normalize obvious activity wording where appropriate.
  Example: "go for a bike ride" -> "cycling"
- Keep locations as recognizable place names.

User message:
"""


def parse_query_with_gemini(query: str) -> ParsedQuery:
    if not query.strip():
        raise ValueError("User query cannot be empty.")

    llm = get_llm()

    response = llm.invoke(
        PARSER_PROMPT + query
    )

    content = response.content

    # Gemini may return text directly or a list of content blocks.
    if isinstance(content, str):
        content = content.strip()

    elif isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if text:
                    text_parts.append(text)

        content = "".join(text_parts).strip()

    else:
        raise ValueError(
            "Gemini returned an unexpected response format."
        )

    if not content:
        raise ValueError(
            "Gemini returned an empty response."
        )

    # Remove Markdown JSON fences if Gemini adds them.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().lower() in ("```json", "```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON."
        ) from exc

    try:
        return ParsedQuery.model_validate(data)

    except ValidationError as exc:
        raise ValueError(
            "Gemini response did not match the expected query format."
        ) from exc