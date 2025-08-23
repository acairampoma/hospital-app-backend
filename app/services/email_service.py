"""
🔐 Servicio de Email con SendGrid
"""
from typing import Optional, Dict, Any
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from app.core.config import settings
import random
import string

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio de email con SendGrid"""
    
    def __init__(self):
        self.sendgrid = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME
    
    async def send_recovery_code(self, email: str, name: str = "Usuario") -> Dict[str, Any]:
        """Enviar código de recuperación"""
        try:
            # Generar código de 6 dígitos
            code = ''.join(random.choices(string.digits, k=6))
            
            # HTML template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #3498db, #27ae60); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px 20px; }}
                    .code-box {{ background: #f1f3f4; border: 2px dashed #3498db; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #3498db; letter-spacing: 5px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏥 IA Medical Solutions</h1>
                        <p>Recuperación de Contraseña</p>
                    </div>
                    <div class="content">
                        <h2>Hola {name},</h2>
                        <p>Recibimos una solicitud para recuperar tu contraseña. Usa el siguiente código:</p>
                        
                        <div class="code-box">
                            <div class="code">{code}</div>
                        </div>
                        
                        <p><strong>Este código es válido por 15 minutos.</strong></p>
                        <p>Si no solicitaste esto, ignora este mensaje.</p>
                    </div>
                    <div class="footer">
                        <p>IA Medical Solutions - Sistema Hospitalario</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(email),
                subject=Subject("🔐 Código de Recuperación - IA Medical"),
                plain_text_content=PlainTextContent(f"Tu código de recuperación es: {code}"),
                html_content=HtmlContent(html_content)
            )
            
            response = self.sendgrid.send(message)
            
            logger.info(f"✅ Email enviado a {email}, código: {code}")
            
            return {
                "success": True,
                "code": code,  # En producción NO devolver el código
                "message": "Código enviado correctamente",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {str(e)}")
            return {
                "success": False,
                "message": f"Error enviando email: {str(e)}",
                "email": email
            }
    
    async def send_welcome_email(self, email: str, name: str, username: str) -> Dict[str, Any]:
        """Enviar email de bienvenida"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #3498db, #27ae60); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px 20px; }}
                    .welcome-box {{ background: #e8f5e8; border-left: 4px solid #27ae60; padding: 20px; margin: 20px 0; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏥 IA Medical Solutions</h1>
                        <p>¡Bienvenido al Sistema!</p>
                    </div>
                    <div class="content">
                        <h2>¡Hola {name}! 👨‍⚕️</h2>
                        <div class="welcome-box">
                            <p><strong>✅ Tu cuenta ha sido creada exitosamente</strong></p>
                            <p><strong>Usuario:</strong> {username}</p>
                            <p><strong>Email:</strong> {email}</p>
                        </div>
                        
                        <p>Ya puedes acceder al sistema hospitalario con todas las funcionalidades disponibles.</p>
                        
                        <p><strong>¿Qué puedes hacer ahora?</strong></p>
                        <ul>
                            <li>🏥 Gestionar pacientes</li>
                            <li>📋 Crear historias clínicas</li>
                            <li>💊 Administrar recetas médicas</li>
                            <li>📊 Ver reportes y estadísticas</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>IA Medical Solutions - Sistema Hospitalario</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(email),
                subject=Subject("🎉 Bienvenido a IA Medical Solutions"),
                plain_text_content=PlainTextContent(f"Bienvenido {name}, tu cuenta ha sido creada exitosamente."),
                html_content=HtmlContent(html_content)
            )
            
            response = self.sendgrid.send(message)
            
            logger.info(f"✅ Email de bienvenida enviado a {email}")
            
            return {
                "success": True,
                "message": "Email de bienvenida enviado",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando email de bienvenida: {str(e)}")
            return {
                "success": False,
                "message": f"Error enviando email: {str(e)}",
                "email": email
            }

# Instancia singleton
email_service = EmailService()