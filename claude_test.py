import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

prompt = HUMAN_PROMPT + "Escribe un saludo breve en español." + AI_PROMPT

resp = client.completions.create(
    model="claude-2.1",
    prompt=prompt,
    max_tokens_to_sample=150
)

print(resp.completion)
