from fastapi import APIRouter
from src.services.payment_service import payment
from src.services.database_service import db
import os
from fastapi.responses import JSONResponse

eventrouter = APIRouter(prefix='/event',tags=['event'])

@eventrouter.post('/register-user')
def register_user(data:dict):
    try:
        if data.get("pass_type") == 'delegate_pass':
            cost = int(os.environ['delegate_pass'])
        elif data.get("pass_type") == 'vip_pass':
            cost = int(os.environ['vip_pass'])
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success":False,
                    "message":"Invalid pass type"
                }
            )
        
            
        order = payment.create_order(cost)
    except:
        return JSONResponse(
                        status_code=400,
                        content={
                            "success":False,
                            "message":"Payment Creation Failed"
                        }
                    )
    try:

        response = db.register_user(tabel='event_registrations',data=data,order =order,cost =cost)
    
        return {
            "success":True,
            "data":  response
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Registration Failed: {str(e)}"
            }
        )
   
    


@eventrouter.get('/get-all-users')
def get_all():
    columns, rows = db.get_all_user(table='event_registrations')
    return {
        "success":True,
        "rows":rows,
        "clumns":columns
    }
    
    