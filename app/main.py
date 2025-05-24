from api.v1.endpoints import app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.v1.endpoints:app", host="0.0.0.0", port=8000, reload=True)
