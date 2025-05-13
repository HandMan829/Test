from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def show():
    print{"안녕" : "Hello"}