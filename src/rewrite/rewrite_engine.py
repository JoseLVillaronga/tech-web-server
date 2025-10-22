"""
Motor de Rewrite Engine
Procesa las reglas de rewrite configuradas en virtual_hosts.yaml
"""

from typing import Dict, List, Tuple, Optional
from .rewrite_rule import RewriteRule
from .conditions import FileNotExistsCondition, DirNotExistsCondition


class RewriteEngine:
    """
    Motor de rewrite que procesa reglas de reescritura de URLs
    
    Carga las reglas desde la configuración del virtual host y las aplica
    a las rutas de los requests.
    """
    
    def __init__(self, vhost: Dict, document_root: str):
        """
        Inicializa el motor de rewrite para un virtual host
        
        Args:
            vhost: Configuración del virtual host (dict)
            document_root: Raíz del documento del virtual host
        """
        self.vhost = vhost
        self.document_root = document_root
        self.rules: List[RewriteRule] = []
        self.enabled = False
        
        # Cargar las reglas desde la configuración
        self._load_rules()
    
    def _load_rules(self) -> None:
        """
        Carga las reglas de rewrite desde la configuración del virtual host
        
        Espera una estructura como:
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
        if 'rewrite_rules' not in self.vhost:
            return
        
        rewrite_rules_config = self.vhost.get('rewrite_rules', [])
        
        if not rewrite_rules_config:
            return
        
        self.enabled = True
        
        for rule_config in rewrite_rules_config:
            try:
                # Extraer configuración de la regla
                pattern = rule_config.get('pattern')
                target = rule_config.get('target')
                
                if not pattern or not target:
                    print(f"⚠️  Regla de rewrite incompleta en {self.vhost.get('domain')}: "
                          f"falta 'pattern' o 'target'")
                    continue
                
                query_string = rule_config.get('query_string', '')
                flags = rule_config.get('flags', [])
                
                # Procesar condiciones
                conditions = []
                conditions_config = rule_config.get('conditions', [])
                
                for cond_config in conditions_config:
                    cond_type = cond_config.get('type') if isinstance(cond_config, dict) else cond_config
                    
                    if cond_type == 'file_not_exists':
                        conditions.append(FileNotExistsCondition())
                    elif cond_type == 'dir_not_exists':
                        conditions.append(DirNotExistsCondition())
                    else:
                        print(f"⚠️  Tipo de condición desconocido: {cond_type}")
                
                # Crear la regla
                rule = RewriteRule(
                    pattern=pattern,
                    target=target,
                    query_string=query_string,
                    conditions=conditions,
                    flags=flags
                )
                
                self.rules.append(rule)
                
            except Exception as e:
                print(f"❌ Error cargando regla de rewrite en {self.vhost.get('domain')}: {e}")
    
    def process(
        self,
        request_path: str,
        query_string: str = ""
    ) -> Tuple[str, str]:
        """
        Procesa una ruta de request aplicando las reglas de rewrite
        
        Args:
            request_path: Ruta del request (ej: /usuarios/123)
            query_string: Query string original (ej: "foo=bar")
            
        Returns:
            Tupla (ruta_final, query_string_final)
        """
        if not self.enabled or not self.rules:
            return request_path, query_string
        
        # Aplicar reglas en orden
        current_path = request_path
        current_query = query_string
        
        for rule in self.rules:
            if rule.matches(current_path, self.document_root):
                # Aplicar la regla
                new_path, new_query = rule.apply(current_path, current_query)
                
                # Actualizar path y query
                current_path = new_path
                current_query = new_query
                
                # Si el flag "L" (Last) está presente, detener el procesamiento
                if "L" in rule.flags or "l" in rule.flags:
                    break
        
        return current_path, current_query
    
    def is_enabled(self) -> bool:
        """Retorna True si el motor de rewrite está habilitado"""
        return self.enabled
    
    def get_rules_count(self) -> int:
        """Retorna la cantidad de reglas cargadas"""
        return len(self.rules)
    
    def __repr__(self) -> str:
        """Representación en string del motor"""
        return (
            f"RewriteEngine(domain='{self.vhost.get('domain')}', "
            f"enabled={self.enabled}, "
            f"rules={len(self.rules)})"
        )

