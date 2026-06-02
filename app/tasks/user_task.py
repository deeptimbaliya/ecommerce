from app.core.celery_app import celery_app

@celery_app.task(name="remove_inactive_users")
def remove_inactive_users():
    # This is a placeholder function. In a real application, you would query the database
    # for users who have been inactive for a certain period and remove them.
    print("Removing inactive users...")
    
    from app.core.database import SessionLocal
    from app.models.user import User
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    try:
    
        inactive_threshold = datetime.now(timezone.utc) - timedelta(days=90) 
        inactive_users = db.query(User).filter(User.last_login < inactive_threshold).all()
        
        for user in inactive_users:
            user.is_active = False  

        db.commit()
        print(f"✅ Deactivated {len(inactive_users)} inactive users")
        return {"deactivated": len(inactive_users) }

    finally:        
        db.close()



@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Delete all expired refresh tokens from the database."""
    from app.core.database import SessionLocal
    from app.models.refresh_token import RefreshToken
    from datetime import datetime, timezone
    from app.core.logger import setup_logger

    logger = setup_logger(__name__)
    logger.info("Starting expired token cleanup")

    db = SessionLocal()
    try:
        deleted = db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} expired tokens")
        return {"deleted": deleted}
    except Exception as e:
        db.rollback()
        logger.error(f"Token cleanup failed: {str(e)}")
        raise
    finally:
        db.close()
