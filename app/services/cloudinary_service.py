"""
📷 Servicio de Cloudinary para upload de imágenes
"""
from typing import Optional, Dict, Any
import logging
import cloudinary
import cloudinary.uploader
from app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

class CloudinaryService:
    """Servicio para subir imágenes a Cloudinary"""
    
    def __init__(self):
        # Cloudinary ya está configurado en main.py globalmente
        pass
    
    async def upload_avatar(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """
        Subir avatar de usuario
        """
        try:
            # Generar nombre único
            unique_name = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Upload con transformaciones para avatar
            response = cloudinary.uploader.upload(
                file_content,
                public_id=unique_name,
                folder="hospital/avatars",
                format="jpg",
                transformation=[
                    {'width': 200, 'height': 200, 'crop': 'fill', 'gravity': 'face'},
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ],
                overwrite=True
            )
            
            logger.info(f"✅ Avatar subido para usuario {user_id}: {response['public_id']}")
            
            return {
                "success": True,
                "url": response['secure_url'],
                "public_id": response['public_id'],
                "width": response.get('width'),
                "height": response.get('height'),
                "format": response.get('format'),
                "message": "Avatar subido exitosamente"
            }
            
        except Exception as e:
            logger.error(f"❌ Error subiendo avatar: {str(e)}")
            return {
                "success": False,
                "message": f"Error subiendo imagen: {str(e)}",
                "url": None
            }
    
    async def upload_document(self, file_content: bytes, filename: str, user_id: str, doc_type: str = "general") -> Dict[str, Any]:
        """
        Subir documento médico
        """
        try:
            # Generar nombre único
            unique_name = f"{doc_type}_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Upload con transformaciones para documentos
            response = cloudinary.uploader.upload(
                file_content,
                public_id=unique_name,
                folder=f"hospital/documents/{doc_type}",
                transformation=[
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ],
                overwrite=True
            )
            
            logger.info(f"✅ Documento subido para usuario {user_id}: {response['public_id']}")
            
            return {
                "success": True,
                "url": response['secure_url'],
                "public_id": response['public_id'],
                "width": response.get('width'),
                "height": response.get('height'),
                "format": response.get('format'),
                "message": "Documento subido exitosamente"
            }
            
        except Exception as e:
            logger.error(f"❌ Error subiendo documento: {str(e)}")
            return {
                "success": False,
                "message": f"Error subiendo documento: {str(e)}",
                "url": None
            }
    
    async def delete_image(self, public_id: str) -> Dict[str, Any]:
        """
        Eliminar imagen de Cloudinary
        """
        try:
            response = cloudinary.uploader.destroy(public_id)
            
            logger.info(f"✅ Imagen eliminada: {public_id}")
            
            return {
                "success": True,
                "message": "Imagen eliminada exitosamente",
                "result": response['result']
            }
            
        except Exception as e:
            logger.error(f"❌ Error eliminando imagen: {str(e)}")
            return {
                "success": False,
                "message": f"Error eliminando imagen: {str(e)}"
            }

# Instancia singleton
cloudinary_service = CloudinaryService()