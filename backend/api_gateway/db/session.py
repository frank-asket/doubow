from collections.abc import AsyncGenerator
from contextvars import ContextVar, Token

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from config import settings

# Set in dependencies.get_authenticated_user before DB work; applied each transaction via after_begin.
request_user_ctx: ContextVar[str | None] = ContextVar("request_user_ctx", default=None)


class Base(DeclarativeBase):
    pass


def bind_request_user_for_rls(user_id: str | None) -> Token | None:
    """Call when resolving the Clerk subject; resets with reset_request_user_rls."""
    if user_id is None:
        return None
    return request_user_ctx.set(user_id)


def reset_request_user_rls(token: Token | None) -> None:
    if token is not None:
        request_user_ctx.reset(token)


def _install_rls_session_hook() -> None:
    @event.listens_for(Session, "after_begin")
    def _after_begin(session: Session, _transaction, connection) -> None:  # type: ignore[no-untyped-def]
        uid = request_user_ctx.get()
        if not uid:
            return
        if getattr(connection.dialect, "name", None) != "postgresql":
            return
        connection.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": uid})


def _to_async_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


engine = create_async_engine(_to_async_database_url(settings.database_url), pool_pre_ping=True)
_install_rls_session_hook()
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
