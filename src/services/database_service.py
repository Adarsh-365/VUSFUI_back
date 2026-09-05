from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.core.database import PostgresDB
from datetime import datetime

class CRUDBase():

    def __init__(self):
        self.model = PostgresDB()
    def get_all_user(self,table):
        return  self.model.get_all(table)
       
    # CREATE
    def verify_update(self,tabel,data):
        data = self.model.verify_update(tabel,data)
        return data
        
    def register_user(self, tabel, data, order, cost):
        try:
            amount_in_rupees = int(cost) // 100

            enrollment_data = {
                "name": data.get("name", ""),
                "mob": data.get("mob", ""),
                "email": data.get("email", ""),
                "age": data.get("age", ""),
                "occupation": data.get("occupation", ""),
                "what_do_you_expect": data.get("what_do_you_expect", ""),
                'order_id': order["order_id"],
                'key': order.get("key", ""),
                'pass_type': data.get("pass_type", ""),
                'amount': amount_in_rupees,
                'event_name': data.get("event_name") or data.get("Event_name", ""),
                "currency": order.get("currency", "INR"),
                "timestamp": str(datetime.now().isoformat())
            }
            self.model.insert(tabel, enrollment_data)
            return enrollment_data
            
        except Exception as e:
            print(f"Error registering user: {e}")
            raise e

db = CRUDBase()
    # # GET BY ID
    # def get(
    #     self,
   
    # ) :

    #   pass

    # # GET ALL
    # def get_all(
    
    # ) :

    #   pass

    # # UPDATE
    # def update(
    #     self,
      
    # ) :

    #   pass

    # # DELETE
    # def delete(
    #     self,
       
    # ) :
    #     pass