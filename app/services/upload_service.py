import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.logger import setup_logger
from app.utils.file_validator import validate_file

logger = setup_logger(__name__) 

async def upload_profile_avatar(file: UploadFile, user_id: int) -> str:
    logger.info(f"Uploading avatar for user id={user_id}")
    content = await validate_file(file)

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=f"ecommerce/avatar/{user_id}",
            public_id=f"avatar_{user_id}",
            overwrite=True,
            transformation=[
                {"width": 500, "height": 500, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
                ],
            resource_type="image"
        )
        logger.info(f"Avatar uploaded successfully for user id={user_id}: {result['secure_url']}")
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result["width"],
            "height": result["height"],
            "format": result["format"],
            "size_bytes": result["bytes"]
        }
    
    except Exception as e:
        logger.error(f"Avatar upload failed for user id={user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload avatar: {str(e)}"
            )
    

async def delete_profile_avatar(public_id: str):
    try:
        logger.info(f"Deleting avatar: public_id={public_id}")
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        if result.get("result") != "ok":
            logger.error(f"Avatar deletion failed for public_id={public_id}")
            raise HTTPException(status_code=500, detail="Failed to delete avatar.")
    except Exception as e:
        logger.error(f"Avatar deletion error for public_id={public_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete avatar: {str(e)}")