import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.config_manager import config
from utils.geoip import geoip_manager

class MongoDBClient:
    """Cliente MongoDB para logging del servidor web"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.logs_collection: Optional[AsyncIOMotorCollection] = None
        self.connected = False
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        """Conecta a MongoDB"""
        async with self._connection_lock:
            if self.connected:
                return True
            
            try:
                # Obtener configuración de conexión
                mongo_user = config.get('mongo_user', '')
                mongo_pass = config.get('mongo_pass', '')
                mongo_host = config.get('mongo_host', 'localhost')
                mongo_port = config.get('mongo_port', 27017)
                mongo_db = config.get('mongo_db', 'tech_web_server')

                print(f"🔌 Conectando a MongoDB: {mongo_host}:{mongo_port}")
                print(f"📁 Base de datos objetivo: {mongo_db}")

                # Construir URI de conexión con o sin autenticación
                if mongo_user and mongo_pass:
                    # Usar base de datos admin para autenticación por defecto
                    auth_db = config.get('mongo_auth_db', 'admin')
                    connection_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/?authSource={auth_db}"
                    print(f"🔍 Intentando conexión con autenticación (usuario: {mongo_user}, authSource: {auth_db})...")
                else:
                    connection_uri = f"mongodb://{mongo_host}:{mongo_port}/"
                    print(f"🔍 Intentando conexión sin autenticación...")

                self.client = AsyncIOMotorClient(
                    connection_uri,
                    serverSelectionTimeoutMS=5000,  # 5 segundos timeout de selección
                    connectTimeoutMS=5000,
                    socketTimeoutMS=30000,          # 30 segundos para agregaciones y limpieza
                    maxPoolSize=10
                )

                # Probar conexión
                await self.client.admin.command('ping')
                print("✅ Conexión a MongoDB establecida")
                
                # Configurar base de datos y colección
                self.database = self.client[mongo_db]
                self.logs_collection = self.database.access_logs
                
                # Crear índices para optimizar consultas y TTL de retención
                await self._create_indexes()
                
                self.connected = True
                retention_days = config.get('log_retention_days', 90)
                asyncio.create_task(self.cleanup_old_logs(days=retention_days))
                print("✅ Conexión a MongoDB establecida correctamente")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                print(f"❌ Error conectando a MongoDB: {e}")
                print("⚠️  Continuando sin logging persistente...")
                self.connected = False
                return False
            except Exception as e:
                print(f"❌ Error inesperado conectando a MongoDB: {e}")
                self.connected = False
                return False
    
    async def _create_indexes(self):
        """Crea índices para optimizar consultas y expiración automática (TTL)"""
        try:
            retention_days = config.get('log_retention_days', 90)
            expire_seconds = retention_days * 86400

            # Verificar si existe un índice timestamp previo sin TTL o con distinto TTL
            existing_indexes = await self.logs_collection.index_information()
            if "timestamp_-1" in existing_indexes:
                current_ttl = existing_indexes["timestamp_-1"].get("expireAfterSeconds")
                if current_ttl != expire_seconds:
                    await self.logs_collection.drop_index("timestamp_-1")

            # Índice por timestamp con expiración automática TTL (por defecto 90 días / 3 meses)
            await self.logs_collection.create_index(
                [("timestamp", pymongo.DESCENDING)],
                expireAfterSeconds=expire_seconds
            )
            
            # Índice por virtual_host (para filtrar por dominio)
            await self.logs_collection.create_index("virtual_host")
            
            # Índice por IP (para análisis de tráfico)
            await self.logs_collection.create_index("ip")
            
            # Índice compuesto para consultas complejas
            await self.logs_collection.create_index([
                ("virtual_host", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            print(f"✅ Índices de MongoDB creados correctamente (TTL retención: {retention_days} días)")
            
        except Exception as e:
            print(f"⚠️  Error creando índices: {e}")
    
    async def log_request(self, request_data: Dict[str, Any]) -> bool:
        """Registra una request en MongoDB"""
        if not self.connected or self.logs_collection is None:
            return False
        
        try:
            # Preparar documento para insertar
            log_document = {
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
                "ip": request_data.get('ip', '127.0.0.1'),
                "country_code": request_data.get('country_code', 'XX'),
                "country_name": geoip_manager.get_country_name(request_data.get('country_code', 'XX')),
                "method": request_data.get('method', 'GET'),
                "path": request_data.get('path', '/'),
                "query_string": request_data.get('query_string', ''),
                "status_code": request_data.get('status_code', 200),
                "request_type": request_data.get('request_type', 'static'),
                "virtual_host": request_data.get('virtual_host', 'unknown'),
                "user_agent": request_data.get('user_agent', ''),
                "response_time": request_data.get('response_time', 0.0),
                "content_length": request_data.get('content_length', 0),
                "referer": request_data.get('referer', ''),
                "protocol": request_data.get('protocol', 'HTTP/1.1')
            }
            
            # Insertar documento de forma asíncrona
            await self.logs_collection.insert_one(log_document)
            return True
            
        except Exception as e:
            print(f"❌ Error insertando log en MongoDB: {e}")
            return False
    
    async def get_recent_logs(self, limit: int = 50, virtual_host: Optional[str] = None) -> List[Dict]:
        """Obtiene logs recientes desde MongoDB"""
        if not self.connected or self.logs_collection is None:
            return []
        
        try:
            # Construir filtro
            filter_query = {}
            if virtual_host and virtual_host != 'all':
                filter_query['virtual_host'] = virtual_host
            
            # Consultar logs recientes
            cursor = self.logs_collection.find(filter_query).sort("timestamp", -1).limit(limit)
            logs = await cursor.to_list(length=limit)
            
            # Convertir ObjectId a string para JSON
            for log in logs:
                log['_id'] = str(log['_id'])
                # Convertir timestamp a ISO string con zona horaria UTC
                if isinstance(log.get('timestamp'), datetime):
                    log['timestamp'] = log['timestamp'].isoformat() + 'Z'
            
            return logs
            
        except Exception as e:
            print(f"❌ Error consultando logs: {e}")
            return []
    
    async def get_stats_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas resumidas de los logs"""
        if not self.connected or self.logs_collection is None:
            return {}
        
        try:
            # Fecha límite para estadísticas
            since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
            
            # Pipeline de agregación para estadísticas
            pipeline = [
                {"$match": {"timestamp": {"$gte": since}}},
                {"$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "unique_ips": {"$addToSet": "$ip"},
                    "status_codes": {"$push": "$status_code"},
                    "request_types": {"$push": "$request_type"},
                    "virtual_hosts": {"$push": "$virtual_host"},
                    "countries": {"$push": "$country_code"}
                }}
            ]
            
            result = await self.logs_collection.aggregate(pipeline).to_list(length=1)
            
            if not result:
                return {"total_requests": 0, "unique_ips": 0}
            
            stats = result[0]
            
            # Procesar estadísticas
            return {
                "total_requests": stats.get("total_requests", 0),
                "unique_ips": len(stats.get("unique_ips", [])),
                "status_distribution": self._count_items(stats.get("status_codes", [])),
                "type_distribution": self._count_items(stats.get("request_types", [])),
                "host_distribution": self._count_items(stats.get("virtual_hosts", [])),
                "country_distribution": self._count_items(stats.get("countries", []))
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def _count_items(self, items: List) -> Dict[str, int]:
        """Cuenta ocurrencias de items en una lista"""
        counts = {}
        for item in items:
            counts[str(item)] = counts.get(str(item), 0) + 1
        return counts
    
    async def get_historical_logs(self,
                                 page: int = 1,
                                 limit: int = 50,
                                 filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene logs históricos con filtros avanzados y paginación

        Args:
            page: Número de página (empezando en 1)
            limit: Número de logs por página
            filters: Diccionario con filtros opcionales:
                - start_date: Fecha inicio (ISO string)
                - end_date: Fecha fin (ISO string)
                - ip: IP específica
                - virtual_host: Virtual host específico
                - status_code: Código de estado específico
                - method: Método HTTP específico
                - search_text: Búsqueda de texto en path o user_agent

        Returns:
            Dict con logs, total_count, page, total_pages
        """
        if not self.connected or self.logs_collection is None:
            return {"logs": [], "total_count": 0, "page": page, "total_pages": 0}

        try:
            # Construir query de filtros
            query = {}

            if filters:
                # Filtro por rango de fechas
                date_filter = {}
                if filters.get('start_date'):
                    try:
                        start_date = datetime.fromisoformat(filters['start_date'].replace('Z', '+00:00'))
                        date_filter['$gte'] = start_date
                    except ValueError:
                        pass

                if filters.get('end_date'):
                    try:
                        end_date = datetime.fromisoformat(filters['end_date'].replace('Z', '+00:00'))
                        date_filter['$lte'] = end_date
                    except ValueError:
                        pass

                if date_filter:
                    query['timestamp'] = date_filter

                # Filtros exactos
                if filters.get('ip'):
                    query['ip'] = filters['ip']

                if filters.get('virtual_host') and filters['virtual_host'] != 'all':
                    query['virtual_host'] = filters['virtual_host']

                if filters.get('status_code'):
                    try:
                        query['status_code'] = int(filters['status_code'])
                    except (ValueError, TypeError):
                        pass

                if filters.get('method'):
                    query['method'] = filters['method'].upper()

                # Búsqueda de texto (regex case-insensitive escapando metacaracteres)
                if filters.get('search_text'):
                    escaped_text = re.escape(str(filters['search_text']))
                    query['$or'] = [
                        {'path': {'$regex': escaped_text, '$options': 'i'}},
                        {'user_agent': {'$regex': escaped_text, '$options': 'i'}}
                    ]

            # Contar total de documentos que coinciden
            total_count = await self.logs_collection.count_documents(query)

            # Calcular paginación
            skip = (page - 1) * limit
            total_pages = (total_count + limit - 1) // limit  # Ceiling division

            # Obtener logs con paginación
            cursor = self.logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            logs = await cursor.to_list(length=limit)

            # Convertir ObjectId y datetime para JSON
            for log in logs:
                log['_id'] = str(log['_id'])
                if isinstance(log.get('timestamp'), datetime):
                    log['timestamp'] = log['timestamp'].isoformat() + 'Z'

            return {
                "logs": logs,
                "total_count": total_count,
                "page": page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

        except Exception as e:
            print(f"❌ Error consultando logs históricos: {e}")
            return {"logs": [], "total_count": 0, "page": page, "total_pages": 0}

    async def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Obtiene opciones disponibles para filtros (virtual hosts, IPs frecuentes, etc.)
        """
        if not self.connected or self.logs_collection is None:
            return {}

        try:
            # Pipeline para obtener valores únicos de campos importantes
            pipeline = [
                {"$group": {
                    "_id": None,
                    "virtual_hosts": {"$addToSet": "$virtual_host"},
                    "methods": {"$addToSet": "$method"},
                    "status_codes": {"$addToSet": "$status_code"},
                    "top_ips": {"$addToSet": "$ip"}
                }},
                {"$project": {
                    "virtual_hosts": 1,
                    "methods": 1,
                    "status_codes": 1,
                    "top_ips": {"$slice": ["$top_ips", 20]}  # Limitar a 20 IPs más frecuentes
                }}
            ]

            result = await self.logs_collection.aggregate(pipeline).to_list(length=1)

            if not result:
                return {}

            options = result[0]

            # Limpiar y ordenar opciones
            return {
                "virtual_hosts": sorted([vh for vh in options.get("virtual_hosts", []) if vh]),
                "methods": sorted([m for m in options.get("methods", []) if m]),
                "status_codes": sorted([str(sc) for sc in options.get("status_codes", []) if sc]),
                "top_ips": sorted([ip for ip in options.get("top_ips", []) if ip])
            }

        except Exception as e:
            print(f"❌ Error obteniendo opciones de filtro: {e}")
            return {}

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Limpia logs antiguos que superen los días de retención configurados"""
        if not self.connected or self.logs_collection is None:
            return 0
        
        try:
            # Fecha límite para limpieza
            cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
            
            # Eliminar logs antiguos
            result = await self.logs_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                print(f"🧹 Limpiados {deleted_count} logs antiguos (>{days} días)")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error limpiando logs antiguos: {e}")
            return 0
    
    async def close(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            print("🔌 Conexión a MongoDB cerrada")

# Instancia global del cliente MongoDB
mongodb_client = MongoDBClient()
