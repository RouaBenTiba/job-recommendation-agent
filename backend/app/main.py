from fastapi import FastAPI

app = FastAPI(title="Job Recommender API")


@app.get("/health")
def health():
    return {"status": "ok"}