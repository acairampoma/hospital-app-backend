from fastapi import HTTPException, status

class HospitalException(Exception):
    """Base exception para el sistema hospitalario"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationException(HospitalException):
    """Excepción de autenticación"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)

class ValidationException(HospitalException):
    """Excepción de validación"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)

class NotFoundError(HospitalException):
    """Excepción para recursos no encontrados"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)

class BusinessRuleException(HospitalException):
    """Excepción para reglas de negocio"""
    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class MedicoPermissionException(HospitalException):
    """Excepción para permisos de médico"""
    def __init__(self, message: str = "Médico no autorizado"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)