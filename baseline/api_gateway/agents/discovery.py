class DiscoveryAgent:
    name = 'discovery'

    async def run(self, context: dict) -> dict:
        return {'jobs': []}
