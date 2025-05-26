from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Abilita CORS per comunicare col frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in produzione puoi usare ["https://fpads.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend FP ADS attivo"}