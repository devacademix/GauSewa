# main.py — MVP Backend (Module 1 ONLY)

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid
import base64

from config import cows_col, JWT_SECRET, JWT_EXPIRE
from ai.nose_predictor import predictor


app = FastAPI(title="Gau Sewa MVP API", version="1.0")


# CORS — Flutter app ko access dene ke liye
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

security = HTTPBearer()


# ■■ JWT HELPERS ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


def create_token(user_id: str, role: str = "farmer") -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ■■ ROUTE 1: Login ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


@app.post("/api/auth/login")
async def login(phone: str, otp: str):
    """Demo mein koi bhi 4-digit OTP kaam karta hai"""

    if len(otp) != 4 or not otp.isdigit():
        raise HTTPException(400, "OTP 4 digits ka hona chahiye")

    token = create_token(user_id=phone, role="farmer")

    return {"token": token, "expires_in": JWT_EXPIRE * 60}


# ■■ ROUTE 2: Register New Cow ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


@app.post("/api/cows/register")
async def register_cow(
    nose_photo: UploadFile = File(...),
    owner_name: str = "Farmer",
    owner_phone: str = "",
    breed: str = "Gir",
    age_years: float = 3.0,
    village: str = "",
    district: str = "",
    state: str = "UP",
    user=Depends(verify_token),
):

    image_bytes = await nose_photo.read()

    # Check: Pehle se registered hai?
    result = predictor.identify(image_bytes)

    if result["match"] and result["confidence"] > 90:
        raise HTTPException(400, f"Gaay pehle se registered hai: {result['cow_id']}")

    # Unique cow ID generate karo
    cow_id = f"COW-{str(uuid.uuid4())[:8].upper()}"

    # Photo base64 mein store karo
    photo_b64 = base64.b64encode(image_bytes).decode()

    cow_doc = {
        "cow_id": cow_id,
        "owner_name": owner_name,
        "owner_phone": owner_phone,
        "breed": breed,
        "age_years": age_years,
        "village": village,
        "district": district,
        "state": state,
        "nose_photo": photo_b64,
        "registered_at": datetime.utcnow().isoformat(),
        "health_status": "GREEN",
        "stolen": False,
        "vaccinations": [],
    }

    cows_col.insert_one(cow_doc)

    return {
        "success": True,
        "cow_id": cow_id,
        "message": f"Gaay successfully registered: {cow_id}",
    }


# ■■ ROUTE 3: Identify Cow by Photo ■■■■■■■■■■■■■■■■■■■■■■■■■


@app.post("/api/cows/identify")
async def identify_cow(nose_photo: UploadFile = File(...)):

    image_bytes = await nose_photo.read()

    result = predictor.identify(image_bytes)

    if not result["match"]:
        return {"found": False, "message": "Gaay system mein registered nahi hai"}

    # Full profile fetch karo
    cow = cows_col.find_one({"cow_id": result["cow_id"]}, {"_id": 0, "nose_photo": 0})

    if not cow:
        return {"found": False, "message": "Profile nahi mila"}

    return {"found": True, "confidence": result["confidence"], "cow": cow}


# ■■ ROUTE 4: Get Cow Profile by ID ■■■■■■■■■■■■■■■■■■■■■■■■■


@app.get("/api/cows/{cow_id}")
async def get_cow_profile(cow_id: str):

    cow = cows_col.find_one({"cow_id": cow_id}, {"_id": 0, "nose_photo": 0})

    if not cow:
        raise HTTPException(404, "Gaay nahi mili")

    return cow


# ■■ ROUTE 5: Report Stolen Cow ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


@app.post("/api/cows/{cow_id}/report-stolen")
async def report_stolen(cow_id: str):

    result = cows_col.update_one(
        {"cow_id": cow_id},
        {"$set": {"stolen": True, "stolen_at": datetime.utcnow().isoformat()}},
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Gaay nahi mili")

    return {"success": True, "message": "Chori ki report darj ho gayi"}


# ■■ ROUTE 6: Add Vaccination Record ■■■■■■■■■■■■■■■■■■■■■■■■


@app.post("/api/cows/{cow_id}/vaccinate")
async def add_vaccination(
    cow_id: str, vaccine: str = "FMD", date: str = "", next_due: str = ""
):

    vax = {
        "vaccine": vaccine,
        "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
        "next_due": next_due,
    }

    result = cows_col.update_one({"cow_id": cow_id}, {"$push": {"vaccinations": vax}})

    if result.matched_count == 0:
        raise HTTPException(404, "Gaay nahi mili")

    return {"success": True, "vaccination": vax}


# ■■ ROUTE 7: Get All Cows (Admin) ■■■■■■■■■■■■■■■■■■■■■■■■■■■


@app.get("/api/cows")
async def list_cows(state: str = None, district: str = None):

    query = {}

    if state:
        query["state"] = state

    if district:
        query["district"] = district

    cows = list(cows_col.find(query, {"_id": 0, "nose_photo": 0}).limit(100))

    return {"cows": cows, "count": len(cows)}


# ■■ ROUTE 8: Dashboard Stats ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


@app.get("/api/dashboard")
async def dashboard():

    total = cows_col.count_documents({})
    stolen = cows_col.count_documents({"stolen": True})

    by_state = list(
        cows_col.aggregate([{"$group": {"_id": "$state", "count": {"$sum": 1}}}])
    )

    return {"total_cows": total, "stolen_cows": stolen, "by_state": by_state}


# ■■ RUN SERVER ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
