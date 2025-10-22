"""
Regla de rewrite individual
Representa una regla de reescritura de URL
"""

import re
from typing import List, Tuple, Optional
from .conditions import Condition


class RewriteRule:
    """
    Representa una regla de rewrite individual
    
    Ejemplo de configuración YAML:
    ```yaml
    rewrite_rules:
      - pattern: "^(.*)$"
        target: "/index.php"
        query_string: "url=$1"
        conditions:
          - type: "file_not_exists"
          - type: "dir_not_exists"
    ```
    """
    
    def __init__(
        self,
        pattern: str,
        target: str,
        query_string: str = "",
        conditions: Optional[List[Condition]] = None,
        flags: Optional[List[str]] = None
    ):
        """
        Inicializa una regla de rewrite
        
        Args:
            pattern: Patrón regex para la URL (ej: "^(.*)$")
            target: URL destino (ej: "/index.php")
            query_string: Query string a agregar (ej: "url=$1")
            conditions: Lista de condiciones que deben cumplirse
            flags: Flags de la regla (ej: ["QSA", "L"])
        """
        try:
            self.pattern = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Patrón regex inválido: {pattern}. Error: {e}")
        
        self.pattern_str = pattern
        self.target = target
        self.query_string = query_string
        self.conditions = conditions or []
        self.flags = flags or []
    
    def matches(self, request_path: str, document_root: str) -> bool:
        """
        Verifica si la regla coincide con la ruta del request
        
        Args:
            request_path: Ruta del request (ej: /usuarios/123)
            document_root: Raíz del documento del virtual host
            
        Returns:
            True si el patrón coincide y todas las condiciones se cumplen
        """
        # Verificar que el patrón coincida
        if not self.pattern.match(request_path):
            return False
        
        # Verificar todas las condiciones
        for condition in self.conditions:
            if not condition.evaluate(request_path, document_root):
                return False
        
        return True
    
    def apply(
        self,
        request_path: str,
        original_query: str = ""
    ) -> Tuple[str, str]:
        """
        Aplica la regla de rewrite a la ruta del request
        
        Args:
            request_path: Ruta del request original
            original_query: Query string original
            
        Returns:
            Tupla (ruta_reescrita, query_string_final)
        """
        # Aplicar el patrón de rewrite
        match = self.pattern.match(request_path)
        if not match:
            return request_path, original_query
        
        # Reemplazar el patrón con el target
        rewritten_path = self.pattern.sub(self.target, request_path)
        
        # Procesar query string con capturas del regex
        query = self.query_string
        if match and query:
            # Reemplazar $1, $2, etc. con los grupos capturados
            for i, group in enumerate(match.groups(), 1):
                if group is not None:
                    query = query.replace(f"${i}", group)
        
        # Manejar flag QSA (Query String Append)
        if "QSA" in self.flags or "qsa" in self.flags:
            if original_query:
                query = f"{query}&{original_query}" if query else original_query
        
        return rewritten_path, query
    
    def __repr__(self) -> str:
        """Representación en string de la regla"""
        return (
            f"RewriteRule(pattern='{self.pattern_str}', "
            f"target='{self.target}', "
            f"query_string='{self.query_string}', "
            f"conditions={len(self.conditions)}, "
            f"flags={self.flags})"
        )

