import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


async def categorize(description: str) -> str:
    # TODO: chamar Gemini para categorizar o gasto
    pass


async def get_financial_tip(summary: dict) -> str:
    # TODO: gerar dica financeira baseada no resumo do usuário
    pass
