import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def db_create_student(name: str, roll_number: str, tech_info: str):
    res = supabase.table("students").insert({
        "name": name,
        "roll_number": roll_number,
        "tech_info": tech_info
    }).execute()
    return res.data

def db_get_students(roll_number: str = None):
    query = supabase.table("students").select("*")
    if roll_number:
        query = query.eq("roll_number", str(roll_number))
    res = query.execute()
    return res.data or []

def db_update_student(roll_number: str, name: str = None, tech_info: str = None):
    update_data = {}
    if name:
        update_data["name"] = name
    if tech_info:
        update_data["tech_info"] = tech_info
        
    res = supabase.table("students").update(update_data).eq("roll_number", roll_number).execute()
    return res.data

def db_delete_student(roll_number: str):
    res = supabase.table("students").delete().eq("roll_number", roll_number).execute()
    return res.data