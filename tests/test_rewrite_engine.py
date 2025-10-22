"""
Tests unitarios para el motor de Rewrite Engine
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

# Agregar src al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rewrite.rewrite_engine import RewriteEngine
from rewrite.rewrite_rule import RewriteRule
from rewrite.conditions import FileNotExistsCondition, DirNotExistsCondition


class TestRewriteConditions(unittest.TestCase):
    """Tests para las condiciones de rewrite"""
    
    def setUp(self):
        """Crear directorio temporal para tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.document_root = self.temp_dir
        
        # Crear algunos archivos y directorios de prueba
        Path(self.temp_dir, 'index.html').touch()
        Path(self.temp_dir, 'public').mkdir()
        Path(self.temp_dir, 'public', 'style.css').touch()
    
    def tearDown(self):
        """Limpiar directorio temporal"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_file_not_exists_condition_true(self):
        """Verifica que FileNotExistsCondition retorna True para archivos que no existen"""
        condition = FileNotExistsCondition()
        result = condition.evaluate('/usuarios/123', self.document_root)
        self.assertTrue(result)
    
    def test_file_not_exists_condition_false(self):
        """Verifica que FileNotExistsCondition retorna False para archivos que existen"""
        condition = FileNotExistsCondition()
        result = condition.evaluate('/index.html', self.document_root)
        self.assertFalse(result)
    
    def test_dir_not_exists_condition_true(self):
        """Verifica que DirNotExistsCondition retorna True para directorios que no existen"""
        condition = DirNotExistsCondition()
        result = condition.evaluate('/nonexistent', self.document_root)
        self.assertTrue(result)
    
    def test_dir_not_exists_condition_false(self):
        """Verifica que DirNotExistsCondition retorna False para directorios que existen"""
        condition = DirNotExistsCondition()
        result = condition.evaluate('/public', self.document_root)
        self.assertFalse(result)


class TestRewriteRule(unittest.TestCase):
    """Tests para las reglas de rewrite"""
    
    def setUp(self):
        """Crear directorio temporal para tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.document_root = self.temp_dir
        
        # Crear archivos de prueba
        Path(self.temp_dir, 'index.php').touch()
        Path(self.temp_dir, 'public').mkdir()
    
    def tearDown(self):
        """Limpiar directorio temporal"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_rule_pattern_matching(self):
        """Verifica que el patrón de la regla coincide correctamente"""
        rule = RewriteRule(
            pattern="^(.*)$",
            target="/index.php",
            query_string="url=$1"
        )
        
        self.assertTrue(rule.matches('/usuarios/123', self.document_root))
        self.assertTrue(rule.matches('/api/posts', self.document_root))
        self.assertTrue(rule.matches('/', self.document_root))
    
    def test_rule_with_conditions(self):
        """Verifica que las condiciones se evalúan correctamente"""
        rule = RewriteRule(
            pattern="^(.*)$",
            target="/index.php",
            query_string="url=$1",
            conditions=[
                FileNotExistsCondition(),
                DirNotExistsCondition()
            ]
        )
        
        # Debe coincidir para rutas que no existen
        self.assertTrue(rule.matches('/usuarios/123', self.document_root))
        
        # No debe coincidir para archivos que existen
        self.assertFalse(rule.matches('/index.php', self.document_root))
        
        # No debe coincidir para directorios que existen
        self.assertFalse(rule.matches('/public', self.document_root))
    
    def test_rule_apply_with_capture_groups(self):
        """Verifica que la regla aplica correctamente los grupos capturados"""
        rule = RewriteRule(
            pattern="^(.*)$",
            target="/index.php",
            query_string="url=$1"
        )
        
        path, query = rule.apply('/usuarios/123')
        self.assertEqual(path, '/index.php')
        self.assertEqual(query, 'url=/usuarios/123')
    
    def test_rule_apply_with_qsa_flag(self):
        """Verifica que el flag QSA agrega el query string original"""
        rule = RewriteRule(
            pattern="^(.*)$",
            target="/index.php",
            query_string="url=$1",
            flags=["QSA"]
        )
        
        path, query = rule.apply('/usuarios/123', 'foo=bar&baz=qux')
        self.assertEqual(path, '/index.php')
        self.assertEqual(query, 'url=/usuarios/123&foo=bar&baz=qux')


class TestRewriteEngine(unittest.TestCase):
    """Tests para el motor de rewrite"""
    
    def setUp(self):
        """Crear directorio temporal para tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.document_root = self.temp_dir
        
        # Crear archivos de prueba
        Path(self.temp_dir, 'index.php').touch()
        Path(self.temp_dir, 'public').mkdir()
        Path(self.temp_dir, 'public', 'style.css').touch()
    
    def tearDown(self):
        """Limpiar directorio temporal"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_engine_without_rules(self):
        """Verifica que el motor funciona sin reglas configuradas"""
        vhost = {
            'domain': 'test.local',
            'document_root': self.document_root
        }
        
        engine = RewriteEngine(vhost, self.document_root)
        self.assertFalse(engine.is_enabled())
        
        path, query = engine.process('/usuarios/123', 'foo=bar')
        self.assertEqual(path, '/usuarios/123')
        self.assertEqual(query, 'foo=bar')
    
    def test_engine_with_rules(self):
        """Verifica que el motor procesa las reglas correctamente"""
        vhost = {
            'domain': 'test.local',
            'document_root': self.document_root,
            'rewrite_rules': [
                {
                    'pattern': '^(.*)$',
                    'target': '/index.php',
                    'query_string': 'url=$1',
                    'conditions': [
                        {'type': 'file_not_exists'},
                        {'type': 'dir_not_exists'}
                    ],
                    'flags': ['QSA', 'L']
                }
            ]
        }
        
        engine = RewriteEngine(vhost, self.document_root)
        self.assertTrue(engine.is_enabled())
        self.assertEqual(engine.get_rules_count(), 1)
        
        # Probar con una ruta que no existe
        path, query = engine.process('/usuarios/123', 'foo=bar')
        self.assertEqual(path, '/index.php')
        self.assertEqual(query, 'url=/usuarios/123&foo=bar')
    
    def test_engine_respects_last_flag(self):
        """Verifica que el motor respeta el flag L (Last)"""
        vhost = {
            'domain': 'test.local',
            'document_root': self.document_root,
            'rewrite_rules': [
                {
                    'pattern': '^/api/(.*)$',
                    'target': '/api/index.php',
                    'query_string': 'endpoint=$1',
                    'flags': ['L']
                },
                {
                    'pattern': '^(.*)$',
                    'target': '/index.php',
                    'query_string': 'url=$1',
                    'flags': ['L']
                }
            ]
        }
        
        engine = RewriteEngine(vhost, self.document_root)
        
        # La primera regla debe coincidir y detener el procesamiento
        path, query = engine.process('/api/users')
        self.assertEqual(path, '/api/index.php')
        self.assertEqual(query, 'endpoint=users')


if __name__ == '__main__':
    unittest.main()

