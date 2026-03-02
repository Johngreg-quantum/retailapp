from fastapi import FastAPI, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import models, schemas, shutil
from database import SessionLocal, engine
import os

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Lacoste Team Pulse")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/submit-checkin/")
async def create_submission(
    user_email: str = Form(...),
    section_name: str = Form(...),
    sales_amount: float = Form(...),
    notes: str = Form(None),
    tasks: str = Form(...), # Passed as comma-separated string
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Save the Photo
    file_location = f"uploads/{photo.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(photo.file, file_object)

    # 2. Save to Database
    new_entry = models.Submission(
        user_email=user_email,
        section_name=section_name,
        sales_amount=sales_amount,
        notes=notes,
        tasks_completed=tasks.split(","),
        photo_path=file_location
    )
    db.add(new_entry)
    db.commit()
    
    # 3. Quick Performance Logic
    performance = "On Track" if 600 <= sales_amount <= 800 else "Outside Goal"
    
    return {"status": "Success", "performance_alert": performance}

@app.get("/manager/daily-report/")
def get_manager_report(db: Session = Depends(get_db)):
    today_data = db.query(models.Submission).all() # Simplification for demo
    total_sales = sum(entry.sales_amount for entry in today_data)
    sections_reporting = [entry.section_name for entry in today_data]
    
    all_sections = ["Polo Wall", "Sport", "Fashion", "Woven"]
    missing = list(set(all_sections) - set(sections_reporting))
    
    return {
        "total_store_sales": total_sales,
        "completed_sections": sections_reporting,
        "missing_sections": missing,
        "entries": today_data
    }

@app.post("/auth/magic-link")
async def send_magic_link(email: str, db: Session = Depends(get_db)):
    # 1. Check if user is one of your 4 team members
    allowed_emails = ["ana@lacoste.com", "marcella@lacoste.com", "gio@lacoste.com", "manager@lacoste.com"]
    if email not in allowed_emails:
        raise HTTPException(status_code=403, detail="Not authorized for this store")

    token = create_magic_token(email)
    
    # 2. In a real app, use an Email API (SendGrid/Mailgun)
    # For now, we print it to the console so you can copy-paste it
    magic_url = f"https://your-app-url.com/verify?token={token}"
    print(f"DEBUG: Sending Email to {email} with link: {magic_url}")
    
    return {"msg": "Magic link sent! Check your email."}

@app.get("/auth/verify")
async def verify_login(token: str):
    email = verify_token(token)
    # Generate a long-term session token
    session_token = jwt.encode({"sub": email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": session_token, "token_type": "bearer"}