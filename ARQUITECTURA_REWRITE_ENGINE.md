# 🏗️ Arquitectura del Rewrite Engine

## 📐 Diseño General

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Request                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         web_server.py (handle_request)                      │
│  1. Obtener virtual host                                    │
│  2. Obtener ruta del request                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         RewriteEngine.process()                             │
│  1. Cargar reglas del vhost                                 │
│  2. Aplicar condiciones                                     │
│  3. Aplicar patrones                                        │
│  4. Retornar ruta reescrita                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Resolver archivo/PHP                                │
│  1. Verificar si existe                                     │
│  2. Ejecutar PHP o servir estático                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Estructura de Módulos

### Nuevo Módulo: `src/rewrite/`

```
src/rewrite/
├── __init__.py
├── rewrite_engine.py      # Motor principal
├── rewrite_rule.py        # Clase RewriteRule
├── conditions.py          # Condiciones (file_exists, etc)
├── htaccess_parser.py     # Parser de .htaccess (opcional)
└── utils.py               # Utilidades
```

---

## 🔧 Componentes Principales

### 1. RewriteEngine (rewrite_engine.py)

```python
class RewriteEngine:
    """Motor de reescritura de URLs"""
    
    def __init__(self, vhost: dict, document_root: str):
        self.vhost = vhost
        self.document_root = document_root
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        """Cargar reglas desde vhost o .htaccess"""
        # Opción 1: Desde virtual_hosts.yaml
        if 'rewrite_rules' in self.vhost:
            self.rules = [
                RewriteRule.from_dict(r) 
                for r in self.vhost['rewrite_rules']
            ]
        
        # Opción 2: Desde .htaccess (si existe)
        htaccess_path = f"{self.document_root}/.htaccess"
        if os.path.exists(htaccess_path):
            parser = HTAccessParser()
            self.rules.extend(parser.parse(htaccess_path))
    
    def process(self, request_path: str, 
                query_string: str = "") -> Tuple[str, str]:
        """
        Procesar request y retornar ruta reescrita
        
        Returns:
            (rewritten_path, new_query_string)
        """
        for rule in self.rules:
            if rule.matches(request_path, self.document_root):
                return rule.apply(request_path, query_string)
        
        # Si no hay coincidencia, retornar original
        return request_path, query_string
```

### 2. RewriteRule (rewrite_rule.py)

```python
class RewriteRule:
    """Representa una regla de reescritura"""
    
    def __init__(self, pattern: str, target: str = None,
                 query_string: str = None, conditions: List = None,
                 action: str = "rewrite", status: int = 200):
        self.pattern = re.compile(pattern)
        self.target = target
        self.query_string = query_string
        self.conditions = conditions or []
        self.action = action  # "rewrite", "pass", "redirect"
        self.status = status
    
    def matches(self, request_path: str, document_root: str) -> bool:
        """Verificar si la regla aplica"""
        # Verificar condiciones
        for condition in self.conditions:
            if not condition.check(request_path, document_root):
                return False
        
        # Verificar patrón
        return self.pattern.match(request_path) is not None
    
    def apply(self, request_path: str, 
              query_string: str = "") -> Tuple[str, str]:
        """Aplicar la regla y retornar ruta reescrita"""
        if self.action == "pass":
            return request_path, query_string
        
        # Reemplazar grupos de captura
        match = self.pattern.match(request_path)
        new_path = self.target
        
        for i, group in enumerate(match.groups(), 1):
            new_path = new_path.replace(f"${i}", group)
        
        # Procesar query string
        new_qs = self.query_string or ""
        if query_string:
            new_qs = f"{new_qs}&{query_string}" if new_qs else query_string
        
        return new_path, new_qs
    
    @staticmethod
    def from_dict(data: dict) -> 'RewriteRule':
        """Crear desde diccionario YAML"""
        conditions = [
            Condition.from_dict(c) 
            for c in data.get('conditions', [])
        ]
        return RewriteRule(
            pattern=data['pattern'],
            target=data.get('target'),
            query_string=data.get('query_string'),
            conditions=conditions,
            action=data.get('action', 'rewrite'),
            status=data.get('status', 200)
        )
```

### 3. Conditions (conditions.py)

```python
class Condition:
    """Base para condiciones"""
    
    def check(self, request_path: str, document_root: str) -> bool:
        raise NotImplementedError
    
    @staticmethod
    def from_dict(data: dict) -> 'Condition':
        cond_type = data.get('type')
        if cond_type == 'file_not_exists':
            return FileNotExistsCondition()
        elif cond_type == 'dir_not_exists':
            return DirNotExistsCondition()
        elif cond_type == 'file_exists':
            return FileExistsCondition()
        # ... más tipos

class FileNotExistsCondition(Condition):
    """Condición: archivo no existe"""
    
    def check(self, request_path: str, document_root: str) -> bool:
        file_path = Path(document_root) / request_path.lstrip('/')
        return not file_path.exists() or not file_path.is_file()

class DirNotExistsCondition(Condition):
    """Condición: directorio no existe"""
    
    def check(self, request_path: str, document_root: str) -> bool:
        dir_path = Path(document_root) / request_path.lstrip('/')
        return not dir_path.exists() or not dir_path.is_dir()
```

---

## 🔌 Integración en web_server.py

### Ubicación: Línea ~107 (después de obtener vhost)

```python
# En handle_request()

# Obtener virtual host
vhost = config.get_virtual_host_by_domain(host)

# ✨ NUEVO: Aplicar rewrite rules
if vhost.get('rewrite_rules') or os.path.exists(
    f"{vhost['document_root']}/.htaccess"
):
    rewrite_engine = RewriteEngine(vhost, vhost['document_root'])
    path, query_string = rewrite_engine.process(
        request.path,
        request.query_string
    )
    # Actualizar request con ruta reescrita
    request._path = path
    if query_string:
        request._query_string = query_string

# Continuar con lógica existente...
```

---

## 📊 Flujo de Ejecución

```
1. Request: GET /usuarios/123
   ├─ Host: puntoa.local
   └─ Path: /usuarios/123

2. Obtener vhost: puntoa.local
   └─ document_root: ./public/puntoa

3. Crear RewriteEngine
   └─ Cargar reglas desde virtual_hosts.yaml

4. Procesar reglas:
   ├─ Regla 1: /public/.* → PASS (no aplica)
   ├─ Regla 2: /vendor/.* → PASS (no aplica)
   └─ Regla 3: ^/(.*)$ → MATCH
      ├─ Condición: file_not_exists → TRUE
      ├─ Condición: dir_not_exists → TRUE
      └─ Aplicar: /index.php?route=/usuarios/123

5. Resolver archivo: ./public/puntoa/index.php
   └─ Ejecutar PHP con $_GET['route'] = '/usuarios/123'

6. Respuesta: Contenido generado por index.php
```

---

## 🧪 Tests Unitarios

```python
# tests/test_rewrite_engine.py

def test_file_not_exists_condition():
    cond = FileNotExistsCondition()
    assert cond.check("/nonexistent", "./public/puntoa") == True
    assert cond.check("/index.php", "./public/puntoa") == False

def test_rewrite_rule_matching():
    rule = RewriteRule(
        pattern="^/(.*)$",
        target="/index.php",
        query_string="route=$1",
        conditions=[FileNotExistsCondition()]
    )
    assert rule.matches("/usuarios/123", "./public/puntoa") == True

def test_rewrite_rule_apply():
    rule = RewriteRule(
        pattern="^/(.*)$",
        target="/index.php",
        query_string="route=$1"
    )
    path, qs = rule.apply("/usuarios/123")
    assert path == "/index.php"
    assert qs == "route=/usuarios/123"
```

---

## 🚀 Implementación Recomendada

### Fase 1: Básico (1-2 días)
- [ ] Crear estructura de módulos
- [ ] Implementar RewriteRule
- [ ] Implementar Conditions básicas
- [ ] Integrar en web_server.py
- [ ] Tests unitarios

### Fase 2: Avanzado (3-5 días)
- [ ] Parser .htaccess
- [ ] Más tipos de condiciones
- [ ] Logging/debugging
- [ ] Documentación
- [ ] Tests de integración

### Fase 3: Optimización (1-2 días)
- [ ] Caché de reglas compiladas
- [ ] Benchmarking
- [ ] Optimización de regex
- [ ] Manejo de errores


