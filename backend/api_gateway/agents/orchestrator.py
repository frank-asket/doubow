class OrchestratorAgent:
    name = 'orchestrator'

    async def run(self, context: dict) -> dict:
        return {'status': 'ok', 'context': context}
