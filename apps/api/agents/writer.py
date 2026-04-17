class WriterAgent:
    name = 'writer'

    async def run(self, context: dict) -> dict:
        return {'drafts': []}
