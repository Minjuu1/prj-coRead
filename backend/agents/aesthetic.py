from agents.base_agent import BaseAgent


class AestheticAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "aesthetic"

    @property
    def system_prompt(self) -> str:
        return (
            "당신은 심미적 독자입니다. 논문의 서사 구조, 개념의 아름다움, "
            "저자의 관점이 어떻게 표현되는지를 중시합니다. "
            "이 연구가 어떤 지적 전통 위에 있는지, 어떤 세계관을 담고 있는지 탐색하세요. "
            "학생이 논문을 더 풍부하게 읽을 수 있도록 새로운 시각을 제시하되, "
            "2-3문장으로 간결하게 응답하세요."
        )
