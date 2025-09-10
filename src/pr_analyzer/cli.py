import click
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
from .indexer import build_index, search_index
from .parser import parse_stack_trace
from .analyzer import analyze_stack_trace

app = FastAPI()

class AnalyzeRequest(BaseModel):
    stack_trace: str

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    index_path = getattr(app.state, "index_path", "./index.faiss")
    result = analyze_stack_trace(req.stack_trace, index_path, top_k=3)
    return result

@click.group()
def main():
    pass

@main.command()
@click.option("--repo", required=True, help="Path to repo to index")
@click.option("--index-path", default="./index.faiss")
@click.option("--chunk-size", default=1024, type=int, help="Chunk size for code splitting")
@click.option("--use-openai-embeddings", is_flag=True, default=False, help="Use OpenAI embeddings instead of sentence-transformers")
def index(repo, index_path):
    # note: default chunk and model may be overridden
    from .indexer import build_index

    build_index(repo, index_path)

@main.command()
@click.option("--index-path", default="./index.faiss")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
def serve(index_path, host, port):
    # store index_path in app state for handlers
    app.state.index_path = index_path
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
