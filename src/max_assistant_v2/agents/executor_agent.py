# src/max_assistant_v2/agents/executor_agent.py
class ExecutorAgent:
    def __init__(self, llm):
        self.llm = llm

    def answer(self, user_text: str, context: str, retrieved: list[str]) -> str:
        return self.llm.chat(user_text=user_text, context=context, retrieved=retrieved)
