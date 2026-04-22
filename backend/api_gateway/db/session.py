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


def _connection_refused_message(exc: BaseException) -> str | None:
    """Detect unreachable Postgres so we can print a helpful hint."""
    chain: list[BaseException] = []
    cur: BaseException | None = exc
    while cur is not None and len(chain) < 8:
        chain.append(cur)
        cur = cur.__cause__ or cur.__context__
    for e in chain:
        if isinstance(e, ConnectionRefusedError):
            return (
                "Cannot connect to PostgreSQL (connection refused). "
                "Start Postgres first, then restart the API. From repo root:\n"
                "  docker compose -f backend/infra/docker-compose.yml up -d\n"
                "If your shell is already in backend/, use:\n"
                "  docker compose -f infra/docker-compose.yml up -d\n"
                "Ensure DATABASE_URL matches (default host port is often 5433 → localhost:5433)."
            )
        msg = str(e).lower()
        if "connection refused" in msg or "errno 61" in msg:
            return (
                "Cannot connect to PostgreSQL. Start the database, confirm DATABASE_URL, then restart uvicorn.\n"
                "  (repo root) docker compose -f backend/infra/docker-compose.yml up -d\n"
                "  (from backend/) docker compose -f infra/docker-compose.yml up -d"
            )
    return None


async def init_models() -> None:
    import models  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        hint = _connection_refused_message(exc)
        if hint:
            raise RuntimeError(hint) from exc
        raise
