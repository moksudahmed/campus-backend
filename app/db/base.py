from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


@as_declarative()
class Base:
    id: int
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
