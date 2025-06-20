#!/usr/bin/env python3
"""
Gestor de servicios para el web server
Maneja reinicio inteligente y verificación de estado
"""

import os
import sys
import subprocess
import time
import signal
import psutil
from pathlib import Path
from typing import Optional, Dict, List
import logging

# Importar configuración
sys.path.insert(0, str(Path(__file__).parent))
from letsencrypt_config import WEB_SERVER_CONFIG

class ServiceManager:
    """Gestor de servicios del web server"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.project_root = Path(__file__).parent.parent
        self.main_script = self.project_root / 'main.py'
        
    def _setup_logger(self) -> logging.Logger:
        """Configura logger básico"""
        logger = logging.getLogger('service_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def find_web_server_processes(self) -> List[psutil.Process]:
        """Encuentra procesos del web server"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('main.py' in arg for arg in cmdline):
                        # Verificar que sea nuestro script
                        if any(str(self.project_root) in arg for arg in cmdline):
                            processes.append(proc)
                            self.logger.debug(f"Proceso encontrado: PID {proc.pid}, CMD: {' '.join(cmdline)}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error buscando procesos: {e}")
        
        return processes
    
    def is_web_server_running(self) -> bool:
        """Verifica si el web server está ejecutándose"""
        processes = self.find_web_server_processes()
        running = len(processes) > 0
        
        if running:
            pids = [p.pid for p in processes]
            self.logger.info(f"🟢 Web server ejecutándose (PIDs: {pids})")
        else:
            self.logger.info("🔴 Web server no está ejecutándose")
        
        return running
    
    def stop_web_server(self, timeout: int = 10) -> bool:
        """Detiene el web server de forma controlada"""
        processes = self.find_web_server_processes()
        
        if not processes:
            self.logger.info("ℹ️  Web server ya está detenido")
            return True
        
        self.logger.info(f"🛑 Deteniendo web server ({len(processes)} procesos)...")
        
        # Intentar terminación suave primero (SIGTERM)
        for proc in processes:
            try:
                self.logger.debug(f"Enviando SIGTERM a PID {proc.pid}")
                proc.terminate()
            except psutil.NoSuchProcess:
                continue
            except Exception as e:
                self.logger.warning(f"Error enviando SIGTERM a PID {proc.pid}: {e}")
        
        # Esperar terminación suave
        start_time = time.time()
        while time.time() - start_time < timeout:
            remaining_processes = self.find_web_server_processes()
            if not remaining_processes:
                self.logger.info("✅ Web server detenido correctamente")
                return True
            time.sleep(0.5)
        
        # Si no se detuvo, forzar terminación (SIGKILL)
        remaining_processes = self.find_web_server_processes()
        if remaining_processes:
            self.logger.warning("⚠️  Forzando terminación con SIGKILL...")
            for proc in remaining_processes:
                try:
                    self.logger.debug(f"Enviando SIGKILL a PID {proc.pid}")
                    proc.kill()
                except psutil.NoSuchProcess:
                    continue
                except Exception as e:
                    self.logger.error(f"Error enviando SIGKILL a PID {proc.pid}: {e}")
            
            # Verificar terminación forzada
            time.sleep(1)
            final_processes = self.find_web_server_processes()
            if not final_processes:
                self.logger.info("✅ Web server detenido forzadamente")
                return True
            else:
                self.logger.error("❌ No se pudo detener el web server")
                return False
        
        return True
    
    def start_web_server(self) -> bool:
        """Inicia el web server"""
        if self.is_web_server_running():
            self.logger.warning("⚠️  Web server ya está ejecutándose")
            return True
        
        if not self.main_script.exists():
            self.logger.error(f"❌ Script principal no encontrado: {self.main_script}")
            return False
        
        self.logger.info("🚀 Iniciando web server...")
        
        try:
            # Iniciar proceso en background
            process = subprocess.Popen(
                ['python3', str(self.main_script)],
                cwd=str(self.project_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Desacoplar del proceso padre
            )
            
            # Esperar un momento para verificar que inició correctamente
            time.sleep(2)
            
            # Verificar que el proceso sigue ejecutándose
            if process.poll() is None:
                # Verificar que realmente esté escuchando
                time.sleep(3)  # Dar tiempo para que inicie completamente
                
                if self.is_web_server_running():
                    self.logger.info(f"✅ Web server iniciado correctamente (PID: {process.pid})")
                    return True
                else:
                    self.logger.error("❌ Web server no está respondiendo después del inicio")
                    return False
            else:
                self.logger.error(f"❌ Web server terminó inmediatamente (código: {process.returncode})")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Error iniciando web server: {e}")
            return False
    
    def restart_web_server(self, timeout: int = 30) -> bool:
        """Reinicia el web server de forma inteligente"""
        self.logger.info("🔄 Reiniciando web server...")
        
        # Detener servidor
        if not self.stop_web_server(timeout // 2):
            self.logger.error("❌ No se pudo detener el web server")
            return False
        
        # Esperar un momento antes de reiniciar
        time.sleep(1)
        
        # Iniciar servidor
        if not self.start_web_server():
            self.logger.error("❌ No se pudo iniciar el web server")
            return False
        
        self.logger.info("✅ Web server reiniciado exitosamente")
        return True
    
    def restart_with_systemd(self) -> bool:
        """Intenta reiniciar usando systemd"""
        try:
            restart_cmd = WEB_SERVER_CONFIG['restart_command']
            self.logger.info(f"🔄 Reiniciando con systemd: {' '.join(restart_cmd)}")
            
            result = subprocess.run(
                restart_cmd,
                capture_output=True,
                text=True,
                timeout=WEB_SERVER_CONFIG['restart_timeout']
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Reinicio con systemd exitoso")
                return True
            else:
                self.logger.warning(f"⚠️  Systemd falló: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout en reinicio con systemd")
            return False
        except FileNotFoundError:
            self.logger.warning("⚠️  Systemctl no encontrado")
            return False
        except Exception as e:
            self.logger.error(f"💥 Error con systemd: {e}")
            return False
    
    def smart_restart(self) -> bool:
        """Reinicio inteligente: intenta systemd primero, luego método manual"""
        self.logger.info("🧠 Iniciando reinicio inteligente...")
        
        # Intentar con systemd primero
        if self.restart_with_systemd():
            return True
        
        # Si systemd falla, usar método manual
        self.logger.info("🔄 Systemd falló, usando método manual...")
        return self.restart_web_server()
    
    def get_service_status(self) -> Dict:
        """Obtiene el estado completo del servicio"""
        processes = self.find_web_server_processes()
        
        status = {
            'running': len(processes) > 0,
            'process_count': len(processes),
            'pids': [p.pid for p in processes],
            'memory_usage': 0,
            'cpu_percent': 0.0
        }
        
        if processes:
            try:
                # Calcular uso de memoria y CPU
                total_memory = sum(p.memory_info().rss for p in processes)
                status['memory_usage'] = total_memory
                
                # CPU percent (promedio de todos los procesos)
                cpu_percents = []
                for p in processes:
                    try:
                        cpu_percents.append(p.cpu_percent())
                    except psutil.NoSuchProcess:
                        continue
                
                if cpu_percents:
                    status['cpu_percent'] = sum(cpu_percents) / len(cpu_percents)
                    
            except Exception as e:
                self.logger.debug(f"Error obteniendo métricas: {e}")
        
        return status

if __name__ == '__main__':
    # Prueba del gestor de servicios
    manager = ServiceManager()
    
    print("🔍 Estado del servicio:")
    status = manager.get_service_status()
    print(f"  Ejecutándose: {status['running']}")
    print(f"  Procesos: {status['process_count']}")
    print(f"  PIDs: {status['pids']}")
    print(f"  Memoria: {status['memory_usage'] / 1024 / 1024:.1f} MB")
    print(f"  CPU: {status['cpu_percent']:.1f}%")
