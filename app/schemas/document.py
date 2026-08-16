from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class DocumentOut(BaseModel):
    # from_attributes lets Pydantic read the SQLAlchemy ORM object directly
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    owner_id: int
