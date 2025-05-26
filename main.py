
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta
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
LICENSE_DURATION_DAYS = 7

class LicenseRequest(BaseModel):
    quantity: int

class ConsumeRequest(BaseModel):
    code: str

class DiscardRequest(BaseModel):
    code: str

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
            "created_at": datetime.now().isoformat(),
            "discarded": False,
            "activation_time": None
        }
        existing.append(entry)
        new_codes.append(code)

    save_licenses(existing)
    return {"generated": new_codes}

@app.get("/check-license")
def check_license(code: str):
    licenses = load_licenses()
    now = datetime.now()

    for lic in licenses:
        if lic["code"] == code:
            if lic.get("discarded"):
                return {"valid": False, "reason": "discarded"}
            if lic["activation_time"]:
                activated = datetime.fromisoformat(lic["activation_time"])
                if now > activated + timedelta(days=LICENSE_DURATION_DAYS):
                    return {"valid": False, "reason": "expired"}
            return {"valid": True, "active": bool(lic["activation_time"])}
    return {"valid": False, "reason": "not found"}

@app.post("/consume-license")
def consume_license(req: ConsumeRequest):
    licenses = load_licenses()
    now = datetime.now()

    for lic in licenses:
        if lic["code"] == req.code:
            if lic.get("discarded"):
                raise HTTPException(status_code=400, detail="Licenza disattivata")
            if lic["activation_time"]:
                activated = datetime.fromisoformat(lic["activation_time"])
                if now > activated + timedelta(days=LICENSE_DURATION_DAYS):
                    raise HTTPException(status_code=400, detail="Licenza scaduta")
            if not lic["activation_time"]:
                lic["activation_time"] = now.isoformat()
                save_licenses(licenses)
            return {"status": "active", "code": lic["code"]}
    raise HTTPException(status_code=404, detail="Licenza non trovata")

@app.post("/discard-license")
def discard_license(req: DiscardRequest):
    licenses = load_licenses()
    for lic in licenses:
        if lic["code"] == req.code:
            lic["discarded"] = True
            save_licenses(licenses)
            return {"status": "discarded", "code": lic["code"]}
    raise HTTPException(status_code=404, detail="Licenza non trovata")
