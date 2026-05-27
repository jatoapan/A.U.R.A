from fastapi import FastAPI

app = FastAPI(title="A.U.R.A API")

@app.get("/")
def read_root():
    return {"message": "Welcome to A.U.R.A Fraud Detection API"}
