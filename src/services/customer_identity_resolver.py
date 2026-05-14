from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from src.models import Customer, CustomerIdentity
from src.services.identity_scoring_engine import IdentityScoringEngine, IdentityCandidate
import jellyfish

logger = logging.getLogger(__name__)

class CustomerIdentityResolver:
    """
    Servicio de Resolución de Identidad (El Conector).
    Se encarga de buscar a un cliente basado en sus identificadores (email, teléfono, id externo).
    Si no existe, lo crea unificando los datos disponibles.
    """
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def resolve(
        self, 
        phone: Optional[str] = None, 
        email: Optional[str] = None, 
        external_id: Optional[str] = None,
        national_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> str:
        """
        Busca si existe un cliente y retorna su ID.
        Si no existe, CREA uno nuevo y retorna el ID.
        Prioridad: Exact Match (National ID > Email / Teléfono / External ID).
        Si un cliente existente proporciona un national_id nuevo, se vincula a su perfil.
        """
        if not phone and not email and not external_id and not national_id:
            raise ValueError("Se requiere al menos un identificador (national_id, phone, email o external_id) para resolver.")

        # 1. Construir las condiciones de búsqueda
        conditions = []
        if national_id:
            conditions.append(and_(CustomerIdentity.channel == 'national_id', CustomerIdentity.identifier == national_id))
        if phone:
            conditions.append(and_(CustomerIdentity.channel == 'whatsapp', CustomerIdentity.identifier == phone))
            conditions.append(and_(CustomerIdentity.channel == 'phone', CustomerIdentity.identifier == phone))
        if email:
            conditions.append(and_(CustomerIdentity.channel == 'email', CustomerIdentity.identifier == email))
        if external_id:
            conditions.append(and_(CustomerIdentity.channel == 'external', CustomerIdentity.identifier == external_id))

        # 2. Buscar Identidades existentes en el tenant
        query = select(CustomerIdentity).where(
            and_(
                CustomerIdentity.tenant_id == self.tenant_id,
                or_(*conditions)
            )
        ).order_by(
            # Dar prioridad a coincidencias por national_id
            (CustomerIdentity.channel == 'national_id').desc(),
            CustomerIdentity.created_at.asc() 
        )
        
        result = await self.db.execute(query)
        identities = result.scalars().all()

        if identities:
            # Retorna el primer customer_id encontrado (Unificación)
            resolved_id = str(identities[0].customer_id)
            logger.info(f"[IdentityResolver] Cliente encontrado: {resolved_id} para tenant {self.tenant_id}")
            
            # Si nos pasaron un national_id pero el cliente no lo tenía registrado, lo guardamos ahora.
            # Esto soluciona el caso: "cliente compra primero sin cédula y luego en otra compra sí la da"
            if national_id and not any(i.channel == 'national_id' for i in identities):
                logger.info(f"[IdentityResolver] Actualizando cliente {resolved_id} con nuevo national_id")
                self.db.add(CustomerIdentity(
                    tenant_id=self.tenant_id,
                    customer_id=resolved_id,
                    channel="national_id",
                    identifier=national_id,
                    is_primary=True,
                    confidence_score=1.0
                ))
                await self.db.flush()
                
            return resolved_id
        
        # 3. Búsqueda Probabilística / Fonética (Sprint C.1)
        if name:
            logger.info(f"[IdentityResolver] Buscando match probabilístico para nombre: {name}")
            # Obtener candidatos potenciales en el tenant (limitar por seguridad)
            candidates_query = select(Customer).where(Customer.tenant_id == self.tenant_id).limit(20)
            c_result = await self.db.execute(candidates_query)
            all_customers = c_result.scalars().all()
            
            candidates_data = [
                {"id": str(c.id), "name": c.first_name, "email": c.email, "phone": c.phone}
                for c in all_customers
            ]
            
            target_data = {"name": name, "email": email, "phone": phone, "national_id": national_id}
            best_match = IdentityScoringEngine.find_best_match(target_data, candidates_data)
            
            if best_match:
                logger.info(f"[IdentityResolver] Match probabilístico encontrado: {best_match.customer_id} (Score: {best_match.match_score})")
                return best_match.customer_id

        # 4. Si no existe, crear Cliente Nuevo + Identidad Principal
        logger.info(f"[IdentityResolver] Cliente NO encontrado. Creando perfil para tenant {self.tenant_id}")
        
        new_customer = Customer(
            tenant_id=self.tenant_id,
            first_name="Nuevo Cliente",
            email=email,
            phone=phone,
            lifecycle_stage="lead"
        )
        self.db.add(new_customer)
        await self.db.flush() 
        
        # Crear las identidades correspondientes
        if national_id:
            self.db.add(CustomerIdentity(
                tenant_id=self.tenant_id,
                customer_id=new_customer.id,
                channel="national_id",
                identifier=national_id,
                is_primary=True,
                confidence_score=1.0
            ))
        if phone:
            self.db.add(CustomerIdentity(
                tenant_id=self.tenant_id,
                customer_id=new_customer.id,
                channel="whatsapp",
                identifier=phone,
                is_primary=True,
                confidence_score=1.0
            ))
            
        if email:
            self.db.add(CustomerIdentity(
                tenant_id=self.tenant_id,
                customer_id=new_customer.id,
                channel="email",
                identifier=email,
                is_primary=True if not phone else False,
                confidence_score=1.0
            ))
            
        if external_id:
            self.db.add(CustomerIdentity(
                tenant_id=self.tenant_id,
                customer_id=new_customer.id,
                channel="external",
                identifier=external_id,
                is_primary=True if not phone and not email else False,
                confidence_score=1.0
            ))
            
        await self.db.flush()
        
        return str(new_customer.id)
