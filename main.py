from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse

import models, schemas, shutil
from database import SessionLocal, engine
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lacoste Team Pulse")   # ✅ app first
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/__routes")
def list_routes():
    return [r.path for r in app.routes]



# ✅ route AFTER app exists
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Retail App is live ✅</h2>
    <p>Go to <a href="/docs">/docs</a> or <a href="/dashboard">/dashboard</a></p>
    """
@app.get("/dashboard")
def get_dashboard():
    return FileResponse("dashboard.html")

if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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



from sqlalchemy import func
from datetime import timedelta

@app.get("/manager/weekly-trends/")
def get_weekly_trends(db: Session = Depends(get_db)):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # 1. Total Sales Trend
    weekly_data = db.query(models.Submission).filter(
        models.Submission.timestamp >= seven_days_ago
    ).all()
    
    total_weekly_sales = sum(d.sales_amount for d in weekly_data)
    
    # 2. Section Performance (The "Leaderboard")
    # This groups sales by section so you see what's actually selling
    section_performance = {}
    for entry in weekly_data:
        if entry.section_name not in section_performance:
            section_performance[entry.section_name] = 0
        section_performance[entry.section_name] += entry.sales_amount

    # 3. The "Underperformer" Alert
    # Automatically flags sections that are averaging < $600/day
    alerts = []
    for section, total in section_performance.items():
        avg = total / 7 # Simple daily average
        if avg < 600:
            alerts.append(f"⚠️ {section} is underperforming. Avg: ${avg:.2f}/day")

    return {
        "weekly_store_total": total_weekly_sales,
        "performance_by_section": section_performance,
        "management_alerts": alerts,
        "strategy_tip": "Focus training on sections with 'Underperforming' alerts."
    }


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your domain
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/manager/weekly-trends/")
def get_trends(db: Session = Depends(get_db)):
    # This feeds the "Weekly Sales Total" and "Section Performance"
    return {
        "weekly_store_total": 0.00, 
        "performance_by_section": {"Polo Wall": 0, "Footwear": 0},
        "management_alerts": ["No data yet - submit your first check-in!"]
    }

@app.get("/manager/daily-report/")
def get_daily_report(db: Session = Depends(get_db)):
    # This feeds the "Live Store View" photo gallery
    return db.query(models.Submission).all()



from fastapi.responses import FileResponse

@app.get("/")
def get_dashboard():
    return FileResponse("index.html")

@app.get("/upload")
def get_upload_page():
    return FileResponse("upload.html")

@app.get("/manager/daily-report/")
def get_daily_report(db: Session = Depends(get_db)):
    # This pulls every submission from your database to show on the dashboard
    return db.query(models.Submission).all()

@app.get("/")
def read_root():
    return {"status": "Pulse Engine is Online"}


from fastapi.responses import FileResponse

# 1. The Manager View (Dashboard)
@app.get("/")
def get_dashboard():
    return FileResponse("index.html")

# 2. The Associate View (Upload Form)
@app.get("/upload")
def get_upload_page():
    return FileResponse("upload.html")

# 3. The Data Feed for the Dashboard
@app.get("/manager/daily-report/")
def get_daily_report(db: Session = Depends(get_db)):
    return db.query(models.Submission).all()