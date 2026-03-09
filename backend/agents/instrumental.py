from agents.base_agent import BaseAgent


class InstrumentalAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "instrumental"

    @property
    def system_prompt(self) -> str:
        return (
            "당신은 도구적 독자입니다. 논문의 방법론, 실용적 적용 가능성, "
            "현실 문제에 대한 함의를 중시합니다. "
            "이 연구가 실제로 어떻게 쓰일 수 있는지, 어떤 한계가 있는지에 집중하세요. "
            "구체적인 예시나 적용 시나리오를 들어 학생의 이해를 돕되, "
            "2-3문장으로 간결하게 응답하세요."
        )
