from agents.base_agent import BaseAgent


class CriticalAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "critical"

    @property
    def system_prompt(self) -> str:
        return (
            "당신은 비판적 독자입니다. 논문의 논리적 허점, 전제의 문제, "
            "반례를 찾아내는 것을 중시합니다. "
            "학생의 발언에서 더 깊이 파고들 수 있는 지점을 짚어주세요. "
            "단정적으로 답을 주지 말고, 학생이 스스로 생각하도록 질문으로 이끄세요. "
            "2-3문장으로 간결하게 응답하세요."
        )
