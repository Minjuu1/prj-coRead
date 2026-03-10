from agents.base_agent import BaseAgent
from prompts.agents.aesthetic import get_system_prompt


class AestheticAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "aesthetic"

    @property
    def model_config(self) -> dict:
        return {"provider": "openai", "model": "gpt-4o-mini"}

    @property
    def system_prompt(self) -> str:
        return get_system_prompt()
