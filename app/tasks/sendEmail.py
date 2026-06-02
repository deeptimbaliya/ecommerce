from app.core.celery_app import celery_app
import time
from fastapi_mail import MessageSchema, MessageType

@celery_app.task(
    bind=True,
    name="send_welcome_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email(self, email: str,name:str):
    try:
        import asyncio
        from app.core.email import fast_mail, render_template
        from app.core.config import settings

        html_content = render_template("welcome.html", {
            "name": name,
            "email": email,
            "app_name": settings.APP_NAME,
            "login_url": "http://localhost:8000/docs",
        })

        message = MessageSchema(
            subject=f"Welcome to {settings.APP_NAME}! 🎉",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )
        asyncio.get_event_loop().run_until_complete(
            fast_mail.send_message(message)
        )
        
        print(f"Welcome email sent to {email}!")
        return {"status": "success", "email": email}
    except Exception as e:
        print(f"Error sending welcome email to {email}: {e}")
        print (f"Retrying in 60 seconds...")
        raise self.retry(exc=e)
    


@celery_app.task(
    bind=True,
    name="send_password_reset_email",
    max_retries=3,
    default_retry_delay=60,
)    
def send_password_reset_email(self, email: str, name: str, token: str):
    try:
        import asyncio
        from app.core.email import fast_mail, render_template
        from app.core.config import settings

        reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"

        html_content = render_template("reset_password.html", {
            "name": name,
            "app_name": settings.APP_NAME,
            "reset_url": reset_link,
        })

        message = MessageSchema(
            subject=f"{settings.APP_NAME} Password Reset Request",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )
        
        asyncio.run(fast_mail.send_message(message))

        print(f"Password reset email sent to {email}!")
        return {"status": "success", "email": email}
    except Exception as e:
        print(f"Error sending password reset email to {email}: {e}")
        print (f"Retrying in 60 seconds...")
        raise self.retry(exc=e)
