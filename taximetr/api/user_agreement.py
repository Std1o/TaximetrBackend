from fastapi import APIRouter, UploadFile, Request
from fastapi.params import Depends
from fastapi.responses import FileResponse, PlainTextResponse
import shutil
import os
import re

from taximetr.service.user_agreement_service import UserAgreementService

router = APIRouter(prefix='/user_agreement', tags=["user_agreement"])

@router.get('/{file_name}')
def get_file(file_name: str):
    return FileResponse(f"taximetr/files/{file_name}".encode('utf-8').decode('utf-8'))

@router.post("/upload/")
async def create_upload_file(request: Request, upload_file: UploadFile):
    try:
        file_path = f"taximetr/files/{upload_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    base_url = str(request.base_url).rstrip('/')
    return PlainTextResponse(f"{base_url}/files/{upload_file.filename}")

@router.get("/")
def get_user_agreement(service: UserAgreementService = Depends()):
    return service.get_user_agreement()

@router.post("/")
def create_user_agreement(file_url: str, service: UserAgreementService = Depends()):
    service.create_user_agreement(file_url)