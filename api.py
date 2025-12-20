#!/usr/bin/python3

'''
Fast API to query the sqlite database and return information user and admin dashboards
'''
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from models.db_handler import DatabaseHandler
from fastapi.responses import FileResponse
from auth import check_current_user, admin_required_api
from pydantic import BaseModel
import os


# Initialize the Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="BrokenRx API")

# Configure CORS (adjust origins for your dashboard deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdateRequest(BaseModel):
    status: str

ALLOWED_STATUSES = {
    "unchecked",
    "approved",
    "in_route",
    "delivered",
    "rejected"
}


@app.get("/me")
def me(user=Depends(check_current_user)):
    return {
        "id": user["user_id"],
        "role": user["role"]
    }

@app.get("/api/admin/prescriptions")
def all_prescriptions(admin=Depends(admin_required_api)):
    with DatabaseHandler() as db:
        prescriptions = db.retrieve_all_prescriptions()
        aggregate = db.aggregate_user_info()

    prescription_list = []
    
    for i in range(len(prescriptions)):
        detail = {
            'id': '',
            'user_id': 0,
            'status': "",
            'is_dispensed': 0,
            'created_at': "",
            'updated_at': ""
        }
        detail["id"] = prescriptions[i][0]
        detail["user_id"] = prescriptions[i][1]
        detail["status"] = prescriptions[i][3]
        detail["created_at"] = prescriptions[i][4]
        detail["updated_at"] = prescriptions[i][5]
        detail["is_dispensed"] = prescriptions[i][6]

        with DatabaseHandler() as db:
            user_profile = db.get_user_profile(detail["user_id"])
        
        
        detail["username"] = user_profile[0][1]
        detail["email"] = user_profile[0][2]

        prescription_list.append(detail)

    aggregate_final = {}
    for i in range(len(aggregate)):
        aggregate_final[aggregate[i][0]] = aggregate[i][1]

    presc = []
    presc.append((list(reversed(prescription_list))))
    presc.append(aggregate_final)
    return presc


@app.get("/api/prescriptions/{user_id}")
def prescriptions(user_id):
    with DatabaseHandler() as db:
        prescriptions = db.retrieve_user_prescription(user_id)
    
    prescription_list = []
    
    if not prescriptions:
        return None

    for i in range(len(prescriptions)):
        detail = {
            'id': '',
            'user_id': 0,
            'status': "",
            'is_dispensed': 0,
            'created_at': "",
            'updated_at': "",
            "is_dispensed": 0
        }
        detail["id"] = prescriptions[i][0]
        detail["user_id"] = prescriptions[i][1]
        detail["status"] = prescriptions[i][3]
        detail["created_at"] = prescriptions[i][4]
        detail["updated_at"] = prescriptions[i][5]
        detail["is_dispensed"] = prescriptions[i][6]

        prescription_list.append(detail)
    return list(reversed(prescription_list))


@app.get("/api/prescription/{prescription_id}/file")
def get_prescription_file(prescription_id):

    with DatabaseHandler() as db:
        prescription = db.retrieve_prescription_path(prescription_id)

    if not prescription:
        raise HTTPException(status_code=404, detail="Not Found")

    file_path = prescription[0]

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File does not exist")

    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg"]:
        media_type = f"image/{ext[1:]}"
    elif ext == ".pdf":
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"

    return FileResponse(path=file_path, media_type=media_type, filename=None)

@app.patch("/api/admin/prescriptions/{prescription_id}/status")
def update_prescription_status(
    prescription_id,
    payload: StatusUpdateRequest
    ):
    '''
    user = check_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin Level Access Required")'''
    new_status = payload.status

    with DatabaseHandler() as db:
        current_status = db.retrieve_prescription_by_id(prescription_id)
    
    if current_status[0][3] == 'rejected' or current_status[0][3] == 'delivered':
        raise HTTPException(status_code=401, detail="Can not Update Status! Prescription either Rejected or Delived")

    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    with DatabaseHandler() as db:
        updated = db.update_status(prescription_id, new_status)

    if not updated:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return {
        "message": "Status updated",
        "prescription_id": prescription_id,
        "new_status": new_status
    }
