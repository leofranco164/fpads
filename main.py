
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "licenses.json"

class LicenseRequest(BaseModel):
    quantity: int

def load_licenses():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.get("/")
def root():
    return {"message": "Backend FP ADS attivo"}

@app.get("/license-list")
def get_license_list():
    data = load_licenses()
    return data

@app.post("/generate-licenses")
def generate_licenses(request: LicenseRequest):
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantità non valida")

    existing = load_licenses()
    new_codes = []

    for _ in range(request.quantity):
        code = str(uuid4()).replace("-", "").upper()[:16]
        entry = {
            "code": code,
            "used": False,
            "created_at": datetime.now().isoformat()
        }
        existing.append(entry)
        new_codes.append(code)

    save_licenses(existing)
    return {"generated": new_codes}

@app.get("/check-license")
def check_license(code: str):
    licenses = load_licenses()
    for lic in licenses:
        if lic["code"] == code:
            if lic["used"]:
                return {"valid": False, "reason": "already used"}
            lic["used"] = True  # contrassegna come usato alla prima attivazione
            save_licenses(licenses)
            return {"valid": True, "used": False}
    return {"valid": False, "reason": "not found"}
