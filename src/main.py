from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

allow_origins = [
    "https://www.namasteindiagroup.org",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from src.api_routes import include_routes

include_routes(app)