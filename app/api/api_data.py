from typing import List, Dict, Optional

from fastapi import APIRouter

from app.utils import password_util

router = APIRouter()


@router.get("/users", response_model=List[Dict[str, str]])
async def get_data():
    data = [
        {"email": "anhph59@fpt.edu.vn", "name": "Pham Hoang Anh"},
        {"email": "anhtvhe176717@fpt.edu.vn", "name": "Tran Van Anh"},
        {"email": "thinhlqhe172306@fpt.edu.vn", "name": "Thinh Le"},
        {"email": "anhtn23@fpt.edu.vn", "name": "Nguyen Thi Anh"},
        {"email": "binhtv95@fpt.edu.vn", "name": "Tran Van Binh"},
        {"email": "cuongnv03@fpt.edu.vn", "name": "Nguyen Van Cuong"},
        {"email": "dungnt88@fpt.edu.vn", "name": "Nguyen Thi Dung"},
        {"email": "duongvk21@fpt.edu.vn", "name": "Vu Khac Duong"},
        {"email": "phongnt90@fpt.edu.vn", "name": "Nguyen Thanh Phong"},
        {"email": "huongtt75@fpt.edu.vn", "name": "Tran Thi Huong"},
        {"email": "hunglm99@fpt.edu.vn", "name": "Le Minh Hung"},
        {"email": "ngant95@fpt.edu.vn", "name": "Nguyen Thi Ngan"},
        {"email": "minhnv68@fpt.edu.vn", "name": "Nguyen Van Minh"},
        {"email": "lannt92@fpt.edu.vn", "name": "Nguyen Thi Lan"},
        {"email": "lucnv01@fpt.edu.vn", "name": "Nguyen Van Luc"},
        {"email": "maitt85@fpt.edu.vn", "name": "Nguyen Thi Mai"},
        {"email": "namnt77@fpt.edu.vn", "name": "Nguyen Thanh Nam"},
        {"email": "ngantt02@fpt.edu.vn", "name": "Ngo Thi Nga"},
        {"email": "phongnv89@fpt.edu.vn", "name": "Nguyen Van Phong"},
        {"email": "quangtr96@fpt.edu.vn", "name": "Tran Van Quang"},
        {"email": "thunt87@fpt.edu.vn", "name": "Nguyen Thi Thu"},
        {"email": "tungnv55@fpt.edu.vn", "name": "Nguyen Van Tung"},
        {"email": "tamnv80@fpt.edu.vn", "name": "Nguyen Van Tam"},
        {"email": "thanhdt59@fpt.edu.vn", "name": "Dao Thi Thanh"}
    ]
    return data

@router.get("/password/{password}", response_model=str)
async def get_data(password: Optional[str] = ""):
    return password_util.hash_password(password)
