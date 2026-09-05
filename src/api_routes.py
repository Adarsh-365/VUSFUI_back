from src.api.event import eventrouter
from src.api.payment import paymentrounter

def include_routes(app):
    app.include_router(eventrouter)
    app.include_router(paymentrounter)