from app.services.llm_service import get_llm


llm = get_llm()

try:
    response = llm.invoke(
        "Reply with exactly: Gemini connection successful"
    )

    print("STATUS: Gemini request successful")
    print("RESPONSE:", response.content)

except Exception as e:
    print("STATUS: Gemini request failed")
    print("ERROR:", e)