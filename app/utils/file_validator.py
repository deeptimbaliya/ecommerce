from fastapi import UploadFile, HTTPException


ALLOWED_IMAGE_TYPES  = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def validate_file(file: UploadFile)-> bytes:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only JPEG, PNG, and WEBP are allowed.")
    
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum limit of 5 MB.")
    
    await file.seek(0)  
    return content