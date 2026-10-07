from fastapi import FastAPI

app = FastAPI(title="Job Recommender API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
