class ApplyAgent:
    name = 'apply'

    async def run(self, context: dict) -> dict:
        return {'applied': False}
