from src.api.event import eventrouter
from src.api.payment import paymentrounter
from src.api.auth import authrouter

def include_routes(app):
    app.include_router(authrouter)
    app.include_router(eventrouter)
    app.include_router(paymentrounter)