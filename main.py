from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import player_register, player_time
from database import engine, Base

# Create the database tables
try:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI()

app.include_router(player_register.router)
app.include_router(player_time.router)

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)