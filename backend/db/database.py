from typing import Optional, List, Type, TypeVar
from sqlmodel import Session, SQLModel, create_engine, select

DATABASE_URL = "sqlite:///server.db"
T = TypeVar("T", bound=SQLModel)

class Database:
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url)
        SQLModel.metadata.create_all(self.engine)

    def add(self, obj: T) -> bool:
        try:
            with Session(self.engine) as session:
                session.add(obj)
                session.commit()
            return True
        except Exception as e:
            print(f"Error adding {obj.__class__.__name__}: {e}")
            return False

    def get_all(self, model: Type[T]) -> List[T]:
        try:
            with Session(self.engine) as session:
                objects = session.exec(select(model)).all()
            return objects
        except Exception as e:
            print(f"Error retrieving {model.__name__}: {e}")
            return []

    def get_by_id(self, model: Type[T], obj_id: int) -> Optional[T]:
        try:
            with Session(self.engine) as session:
                obj = session.exec(select(model).where(model.id == obj_id)).one_or_none()
            return obj
        except Exception as e:
            print(f"Error retrieving {model.__name__} by ID: {e}")
            return None

    def get_by_urls(self, model: Type[T], urls: List[str]) -> List[T]:
        try:
            with Session(self.engine) as session:
                objects = session.exec(select(model).where(model.url.in_(urls))).all()
            return objects
        except Exception as e:
            print(f"Error retrieving {model.__name__} by URLs: {e}")
            return []

    def update(self, model: Type[T], obj_id: int, data: dict) -> bool:
        try:
            with Session(self.engine) as session:
                obj = session.exec(select(model).where(model.id == obj_id)).one_or_none()
                if obj:
                    for key, value in data.items():
                        setattr(obj, key, value)
                    session.add(obj)
                    session.commit()
                    return True
            return False
        except Exception as e:
            print(f"Error updating {model.__name__}: {e}")
            return False

    def delete(self, model: Type[T], obj_id: int) -> bool:
        try:
            with Session(self.engine) as session:
                obj = session.exec(select(model).where(model.id == obj_id)).one_or_none()
                if obj:
                    session.delete(obj)
                    session.commit()
                    return True
            return False
        except Exception as e:
            print(f"Error deleting {model.__name__}: {e}")
            return False