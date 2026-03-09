from agents.critical import CriticalAgent
from agents.instrumental import InstrumentalAgent
from agents.aesthetic import AestheticAgent
from agents.base_agent import BaseAgent

_agents: dict[str, BaseAgent] = {
    "critical": CriticalAgent(),
    "instrumental": InstrumentalAgent(),
    "aesthetic": AestheticAgent(),
}

# 순서대로 돌아가며 응답 (Phase C에서 실제 라우팅 로직으로 교체)
_turn = 0


def get_next_agent() -> BaseAgent:
    global _turn
    order = ["critical", "instrumental", "aesthetic"]
    agent = _agents[order[_turn % 3]]
    _turn += 1
    return agent


def get_agent(agent_id: str) -> BaseAgent:
    return _agents[agent_id]
