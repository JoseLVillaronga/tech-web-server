"""
Condiciones para reglas de rewrite
Implementa las condiciones que deben cumplirse para aplicar una regla
"""

from pathlib import Path
from abc import ABC, abstractmethod


class Condition(ABC):
    """Clase base para todas las condiciones de rewrite"""
    
    @abstractmethod
    def evaluate(self, request_path: str, document_root: str) -> bool:
        """
        Evalúa si la condición se cumple
        
        Args:
            request_path: Ruta del request (ej: /usuarios/123)
            document_root: Raíz del documento del virtual host
            
        Returns:
            True si la condición se cumple, False en caso contrario
        """
        pass


class FileNotExistsCondition(Condition):
    """Condición: el archivo NO existe en el filesystem"""
    
    def evaluate(self, request_path: str, document_root: str) -> bool:
        """
        Verifica que el archivo NO existe
        
        Args:
            request_path: Ruta del request
            document_root: Raíz del documento
            
        Returns:
            True si el archivo NO existe
        """
        try:
            # Limpiar la ruta
            clean_path = request_path.lstrip('/')
            
            # Construir ruta completa
            file_path = Path(document_root) / clean_path
            
            # Resolver para evitar path traversal
            file_path = file_path.resolve()
            document_root_resolved = Path(document_root).resolve()
            
            # Verificar que está dentro del document_root
            if not str(file_path).startswith(str(document_root_resolved)):
                return True  # Si está fuera, consideramos que "no existe"
            
            # Retornar True si NO es un archivo
            return not file_path.is_file()
        except (OSError, ValueError):
            return True  # Si hay error, consideramos que no existe


class DirNotExistsCondition(Condition):
    """Condición: el directorio NO existe en el filesystem"""
    
    def evaluate(self, request_path: str, document_root: str) -> bool:
        """
        Verifica que el directorio NO existe
        
        Args:
            request_path: Ruta del request
            document_root: Raíz del documento
            
        Returns:
            True si el directorio NO existe
        """
        try:
            # Limpiar la ruta
            clean_path = request_path.lstrip('/')
            
            # Construir ruta completa
            dir_path = Path(document_root) / clean_path
            
            # Resolver para evitar path traversal
            dir_path = dir_path.resolve()
            document_root_resolved = Path(document_root).resolve()
            
            # Verificar que está dentro del document_root
            if not str(dir_path).startswith(str(document_root_resolved)):
                return True  # Si está fuera, consideramos que "no existe"
            
            # Retornar True si NO es un directorio
            return not dir_path.is_dir()
        except (OSError, ValueError):
            return True  # Si hay error, consideramos que no existe

