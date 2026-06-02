from fastapi_mail import FastMail, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.core.config import settings


mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


fast_mail = FastMail(mail_config)

jinja_env = Environment(
    loader=FileSystemLoader(
        Path(__file__).parent.parent / "templates" / "emails"
    )
    )

def render_template(template_name: str, context: dict) -> str:
    """Render an HTML email template with context variables."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)