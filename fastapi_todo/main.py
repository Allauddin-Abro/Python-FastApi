# importing libraries
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from fastapi_todo import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException

# defining table structure and data model
class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)

# connection string
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)
# recycle connection
engine = create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)

# creating tables defined in structure
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# life span method 
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield

# app defination and details
app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://0.0.0.0:8000",
            "description": "Development Server"
        }
        ])

# databse session stablishment
def get_session():
    with Session(engine) as session:
        yield session


# rooot rout 
@app.get("/")
def read_root():
    return {"Hello": "Backend Developer"}


# defining post request on todos end point (insert todo)
@app.post("/todos/", response_model=Todo)
def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)]):
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


# defining get request on todos end point (select * todo)
@app.get("/todos/", response_model=list[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
        todos = session.exec(select(Todo)).all()
        return todos


# defining put request on todos end point (update todo)
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updated_todo: Todo, session: Annotated[Session, Depends(get_session)]):
    select_todo = session.exec(select(Todo).where(Todo.id == todo_id)).first()
    if select_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in updated_todo.dict().items():
        setattr(select_todo, key, value)
    session.add(select_todo)
    session.commit()
    session.refresh(select_todo)
    return select_todo


# defining delete request on todos end point (delete todo)
@app.delete("/todos/{todo_id}",response_model=Todo)
def delete_todo(todo_id: int, session: Annotated[Session, Depends(get_session)]):
    select_todo = session.exec(select(Todo).where(Todo.id == todo_id)).first()
    if select_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(select_todo)
    session.commit()
    return {"message": "Todo deleted"}
