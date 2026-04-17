from schemas.users import MeResponse


async def get_me() -> MeResponse:
    return MeResponse(id="dev-user", email="demo@doubow.ai", name="Franck L.", plan="pro")
