from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for every ORM model. Tables themselves are created by
    the raw SQL migrations under supabase/migrations/, not by
    Base.metadata.create_all() -- these models are query/insert mappings onto
    that already-existing schema."""
