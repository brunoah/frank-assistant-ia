from openai import OpenAI

SYSTEM_DEFAULT = """Tu es FRANK, assistant local type JARVIS.
Réponds en français, utile, concis.
"""

class LMStudioClient:
    def __init__(self, base_url: str, model_id: str):
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
        self.model_id = model_id

    def raw_chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 400,
        top_p: float = 0.8,
    ) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        return (resp.choices[0].message.content or "").strip()


    def chat(
        self,
        user_text: str,
        context: str = "",
        retrieved: list[str] | None = None,
        temperature: float = 0.4,
        max_tokens: int = 400,
        top_p: float = 0.8,
    ) -> str:
        retrieved = retrieved or []
        rag = "\n".join([f"- {x}" for x in retrieved])

        prompt = f"""
    CONTEXTE:
    {context}

    MÉMOIRE RETROUVÉE (peut contenir des infos partielles, à recouper si besoin):
    {rag}

    USER:
    {user_text}
    """

        return self.raw_chat(
            system=SYSTEM_DEFAULT,
            user=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, max_tokens: int = 200) -> str:
        """
        Version spéciale pour le MemoryWriter.
        Injecte le system_prompt dans le contexte.
        """

        combined_context = system_prompt

        # On appelle chat normalement
        response = self.chat(
            user_text=user_prompt,
            context=combined_context,
            retrieved=None
        )

        return response



