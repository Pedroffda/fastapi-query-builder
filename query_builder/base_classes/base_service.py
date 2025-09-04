"""
Base Service for Query Builder Library

Provides common CRUD operations with consistent error handling.
"""

import re
import logging
from typing import Generic, TypeVar, List, Optional, Dict, Any, Literal, Tuple, Type
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..core.query_builder import QueryBuilder
from ..utils.relationship_utils import get_dynamic_relations_map
from ..exceptions.query_builder_exceptions import QueryBuilderException

logger = logging.getLogger(__name__)

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
CreateSchemaType = TypeVar('CreateSchemaType')  # Schema for creating an item
UpdateSchemaType = TypeVar('UpdateSchemaType')  # Schema for updating an item
GenericSchemaType = TypeVar('GenericSchemaType')  # Generic schema for returning an item


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, GenericSchemaType]):
    """
    Base class for all Service classes to reduce code duplication and improve maintainability.

    This class provides common CRUD operations with consistent error handling.
    """

    def __init__(
        self,
        model_class: Type[ModelType],
        entity_name: str,
        relationship_map: Dict[str, Any],
        generic_schema: Type[GenericSchemaType],
        searchable_fields: Optional[List[str]] = None,
        tenant_context_getter: Optional[callable] = None,
    ):
        """
        Initialize the base service with model class and relationship map.

        Args:
            model_class: The SQLAlchemy model class
            entity_name: The name of the entity (used in error messages)
            relationship_map: Dictionary mapping relationship names to SQLAlchemy relationship attributes
            generic_schema: Generic schema class for validation
            searchable_fields: List of fields that can be searched
            tenant_context_getter: Function to get current tenant ID
        """
        self.model_class = model_class
        self.entity_name = entity_name
        self.relationship_map = relationship_map
        self.generic_schema = generic_schema
        self.searchable_fields = searchable_fields or []
        self.tenant_context_getter = tenant_context_getter
        self.query_builder = QueryBuilder()

    def _apply_tenant_filter(self, query):
        """Apply tenant filter if tenant context is available"""
        if not self.tenant_context_getter:
            return query
            
        try:
            tenant_id = self.tenant_context_getter()
        except (LookupError, Exception):
            tenant_id = None

        if tenant_id and hasattr(self.model_class, "tenant_id"):
            query = query.where(self.model_class.tenant_id == tenant_id)
        return query

    def get_by_id(
        self,
        db: Session,
        id: UUID,
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
    ) -> Optional[ModelType]:
        """Get an entity by ID"""
        query = select(self.model_class).where(
            self.model_class.id == id,
            self.model_class.flg_excluido == False
        )
        # Apply tenant filter if needed
        query = self._apply_tenant_filter(query)
        query = self.query_builder.apply_select_load_options(
            query,
            self.model_class,
            include_param=self._merge_include_into_select(select_fields, include)
        )
        result = db.execute(query).scalar_one_or_none()
        
        return result

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
        include: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[Literal["asc", "desc"]] = "asc"
    ) -> Tuple[List[ModelType], int]:
        """Get all entities with pagination, filtering, and sorting"""
        base_query = select(self.model_class).where(self.model_class.flg_excluido == False)
        count_query = select(func.count(self.model_class.id)).where(self.model_class.flg_excluido == False)
        
        # Apply tenant filter
        base_query = self._apply_tenant_filter(base_query)
        count_query = self._apply_tenant_filter(count_query)
        
        # Build query with all operations
        base_query = self.query_builder.build_query(
            base_query,
            self.model_class,
            self.relationship_map,
            search=search,
            search_fields=self.searchable_fields,
            filter_params=filter_params,
            sort_by=sort_by,
            sort_dir=sort_dir,
            include_param=self._merge_include_into_select(select_fields, include)
        )
        
        # Apply same operations to count query
        if search and self.searchable_fields:
            count_query = self.query_builder.apply_search(count_query.select_from(self.model_class), self.model_class, search, self.searchable_fields)
        
        if filter_params:
            count_query = self.query_builder.apply_filters(count_query.select_from(self.model_class), self.model_class, filter_params, self.relationship_map)
        
        total_count = db.execute(count_query).scalar() or 0
        
        query = base_query.offset(skip).limit(limit)
        results = db.execute(query).scalars().all()
        
        return results, total_count

    def create(self, db: Session, data: CreateSchemaType) -> ModelType:
        """Create a new entity"""
        create_data = data.model_dump(exclude_unset=True)
        
        # Ensure tenant_id is automatically filled in for tenant-aware models
        if self.tenant_context_getter:
            try:
                tenant_id = self.tenant_context_getter()
                if hasattr(self.model_class, "tenant_id") and "tenant_id" not in create_data:
                    if not tenant_id:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Header 'tenant_id' is required to create this resource.")
                    create_data["tenant_id"] = tenant_id
            except (LookupError, Exception):
                pass

        db_model = self.model_class(**create_data)
        db.add(db_model)

        try:
            db.flush()
            db.commit()
            db.refresh(db_model)
            
            # Load relationships after create
            relations_to_load_after_create = list(self.relationship_map.keys())
            if relations_to_load_after_create:
                try:
                    db.refresh(db_model, attribute_names=relations_to_load_after_create)
                except Exception as refresh_err:
                    logger.warning(f"Failed to load relationships {relations_to_load_after_create} after creating {self.entity_name} (ID: {db_model.id}): {refresh_err}")
            
        except IntegrityError as e:
            db.rollback()
            raw_msg = str(e.orig)
            match = re.search(r"Key \((.*?)\)=\((.*?)\) already exists", raw_msg)
            if match:
                campo, valor = match.groups()
                user_msg = (
                    f"Já existe {self.entity_name} com {campo}='{valor}'. "
                    "Altere o valor ou utilize outro registro."
                )
            else:
                user_msg = (
                    f"Não foi possível criar {self.entity_name}. "
                    f"Verifique se há violação de valores únicos ou chaves estrangeiras inválidas. {e}"
                )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=user_msg)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error - Create - {str(e)}")

        return db_model

    def update(
        self,
        db: Session,
        id: UUID,
        data: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Update an existing entity"""
        db_model = self.get_by_id(db, id)
        if db_model is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            if hasattr(db_model, key):
                setattr(db_model, key, value)
            else:
                logger.warning(f"Field '{key}' not found in {self.entity_name} model during update.")

        db.add(db_model)
        try:
            db.commit()
            db.refresh(db_model)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity Error when updating {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not update {self.entity_name}. Check for unique value violations or invalid foreign keys."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error when updating {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when updating {self.entity_name}.")

        return db_model

    def delete(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Soft delete an entity by setting flg_excluido to True"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_tenant_filter(query)
        db_model = db.execute(query).scalar_one_or_none()
        
        if db_model is None:
            return None
            
        try:
            db_model.flg_excluido = True
            db.add(db_model)
            db.commit()
            db.refresh(db_model)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity Error when soft deleting {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not soft delete {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error when soft deleting {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when soft deleting {self.entity_name}.")
            
        return db_model

    def restore(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Restore a soft deleted entity by setting flg_excluido to False"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_tenant_filter(query)
        db_model = db.execute(query).scalar_one_or_none()
        
        if db_model is None:
            return None
            
        try:
            db_model.flg_excluido = False
            db.add(db_model)
            db.commit()
            db.refresh(db_model)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity Error when restoring {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not restore {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error when restoring {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when restoring {self.entity_name}.")
            
        return db_model

    def get_deleted(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
        include: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[Literal["asc", "desc"]] = "asc"
    ) -> Tuple[List[ModelType], int]:
        """Get all soft deleted entities with pagination, filtering, and sorting"""
        base_query = select(self.model_class).where(self.model_class.flg_excluido == True)
        count_query = select(func.count(self.model_class.id)).where(self.model_class.flg_excluido == True)
        
        # Apply tenant filter
        base_query = self._apply_tenant_filter(base_query)
        count_query = self._apply_tenant_filter(count_query)
        
        # Build query with all operations
        base_query = self.query_builder.build_query(
            base_query,
            self.model_class,
            self.relationship_map,
            search=search,
            search_fields=self.searchable_fields,
            filter_params=filter_params,
            sort_by=sort_by,
            sort_dir=sort_dir,
            include_param=self._merge_include_into_select(select_fields, include)
        )
        
        # Apply same operations to count query
        if search and self.searchable_fields:
            count_query = self.query_builder.apply_search(count_query.select_from(self.model_class), self.model_class, search, self.searchable_fields)
        
        if filter_params:
            count_query = self.query_builder.apply_filters(count_query.select_from(self.model_class), self.model_class, filter_params, self.relationship_map)
        
        total_count = db.execute(count_query).scalar() or 0
        
        query = base_query.offset(skip).limit(limit)
        results = db.execute(query).scalars().all()
        
        return results, total_count

    def hard_delete(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Hard delete an entity (permanently remove from database)"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_tenant_filter(query)
        db_model = db.execute(query).scalar_one_or_none()
        
        if db_model is None:
            return None
            
        try:
            db.delete(db_model)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity Error when hard deleting {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not hard delete {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error when hard deleting {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when hard deleting {self.entity_name}.")
            
        return db_model

    def _merge_include_into_select(self, select_fields: Optional[str], include: Optional[List[str]]) -> Optional[str]:
        """
        Combina o parâmetro `select` (string) com a lista `include` produzindo
        uma única string compatível com a sintaxe esperada por
        `apply_select_load_options`. Cada relacionamento em `include` é
        convertido para a forma "[rel]" para que seja interpretado como
        relacionamento completo.

        Exemplo:
            select_fields = "id,nome"
            include = ["paciente", "consultas"]
            -> "id,nome,[paciente],[consultas]"
        """
        if not include:
            return select_fields

        include_tokens = ",".join(f"[{rel}]" for rel in include)

        if select_fields:
            return f"{select_fields},{include_tokens}"
        else:
            return include_tokens
