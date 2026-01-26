from langchain_ollama.chat_models import ChatOllama

class OllamaLLM:
    def __init__(self, user_controls_input):
        self.user_controls_input = user_controls_input

    def get_llm_model(self):
        selected_ollama_model = self.user_controls_input.get("selected_ollama_model", "mistral:latest")
        llm = ChatOllama(model=selected_ollama_model, temperature=0.0)
        return llm
