class MonitorAgent:
    name = 'monitor'

    async def run(self, context: dict) -> dict:
        return {'changes': []}
