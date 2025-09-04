"""
Base Use Case for Query Builder Library

Provides common use case operations with consistent error handling and mapping.
"""

import logging
from typing import Generic, TypeVar, List, Optional, Dict, Any, Literal, Callable
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..exceptions.query_builder_exceptions import QueryBuilderException

logger = logging.getLogger(__name__)

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
CreateSchemaType = TypeVar('CreateSchemaType')  # Schema for creating an item
UpdateSchemaType = TypeVar('UpdateSchemaType')  # Schema for updating an item
ViewSchemaType = TypeVar('ViewSchemaType')  # Schema for returning an item


class BaseUseCase(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ViewSchemaType]):
    """
    Base class for all Use Case classes to reduce code duplication and improve maintainability.

    This class provides common CRUD operations with consistent error handling and mapping
    between database models and view models.
    """

    def __init__(
        self,
        service: Any,
        entity_name: str,
        map_to_view: Callable[[ModelType, Optional[List[str]], Optional[str]], Optional[ViewSchemaType]],
        map_list_to_view: Callable[[List[ModelType], Optional[List[str]], Optional[str]], List[ViewSchemaType]]
    ):
        """
        Initialize the base use case with service and mapper functions.

        Args:
            service: The service instance that handles database operations
            entity_name: The name of the entity (used in error messages)
            map_to_view: Function to map a single model to a view model
            map_list_to_view: Function to map a list of models to view models
        """
        self.service = service
        self.entity_name = entity_name
        self.map_to_view = map_to_view
        self.map_list_to_view = map_list_to_view

    async def get_all(
        self,
        db: Session,
        skip: int,
        limit: int,
        include: Optional[List[str]],
        filter_params: Optional[Dict[str, Dict[str, Any]]],
        sort_by: Optional[str],
        sort_dir: Optional[Literal["asc", "desc"]],
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all entities with pagination, filtering, and sorting.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include: Related entities to include
            filter_params: Filtering parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (asc or desc)
            search: Search term
            select_fields: Fields to select for serialization

        Returns:
            Dictionary with total count and list of view models
        """
        try:
            models, total_count = self.service.get_all(
                db=db,
                skip=skip,
                limit=limit,
                include=include,
                filter_params=filter_params,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                select_fields=select_fields,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.get_all: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - {str(e)}")

        view_models = self.map_list_to_view(models, include, select_fields)
        return {"total": total_count, "data": view_models}

    async def create(
        self,
        db: Session,
        data: CreateSchemaType
    ) -> ViewSchemaType:
        """
        Create a new entity.

        Args:
            db: Database session
            data: Data for creating the entity

        Returns:
            View model of the created entity
        """
        try:
            created_model = self.service.create(db=db, data=data)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.create: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - Create - {str(e)}")

        return self.map_to_view(created_model, None, None)

    async def get_by_id(
        self,
        db: Session,
        id: UUID,
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
    ) -> Optional[ViewSchemaType]:
        """
        Get an entity by ID.

        Args:
            db: Database session
            id: Entity ID
            include: Related entities to include
            select_fields: Fields to select for serialization

        Returns:
            View model of the entity or None if not found
        """
        try:
            model = self.service.get_by_id(db=db, id=id, include=include, select_fields=select_fields)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.get_by_id: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - GET - {str(e)}")

        if model is None:
            return None

        mapped = self.map_to_view(model, include, select_fields)
        return {"data": [mapped]}

    async def update(
        self,
        db: Session,
        id: UUID,
        data: UpdateSchemaType
    ) -> Optional[ViewSchemaType]:
        """
        Update an existing entity.

        Args:
            db: Database session
            id: Entity ID
            data: Data for updating the entity

        Returns:
            View model of the updated entity or None if not found
        """
        existing_model = self.service.get_by_id(db=db, id=id)
        if existing_model is None:
            return None

        try:
            updated_model = self.service.update(db=db, id=id, data=data)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.update: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - Update - {str(e)}")

        return self.map_to_view(updated_model, None, None)

    async def delete(
        self,
        db: Session,
        id: UUID
    ) -> Optional[Any]:
        """
        Delete an entity.

        Args:
            db: Database session
            id: Entity ID

        Returns:
            The deleted entity or None if not found
        """
        existing_model = self.service.get_by_id(db=db, id=id)
        if existing_model is None:
            return None

        try:
            deleted_model = self.service.delete(db=db, id=id)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.delete: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - Delete - {str(e)}")

        return deleted_model

    async def restore(
        self,
        db: Session,
        id: UUID
    ) -> Optional[ViewSchemaType]:
        """
        Restore a soft deleted entity.

        Args:
            db: Database session
            id: Entity ID

        Returns:
            View model of the restored entity or None if not found
        """
        try:
            restored_model = self.service.restore(db=db, id=id)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.restore: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - Restore - {str(e)}")

        if restored_model is None:
            return None

        return self.map_to_view(restored_model, None, None)

    async def get_deleted(
        self,
        db: Session,
        skip: int,
        limit: int,
        include: Optional[List[str]],
        filter_params: Optional[Dict[str, Dict[str, Any]]],
        sort_by: Optional[str],
        sort_dir: Optional[Literal["asc", "desc"]],
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all soft deleted entities with pagination, filtering, and sorting.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include: Related entities to include
            filter_params: Filtering parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (asc or desc)
            search: Search term
            select_fields: Fields to select for serialization

        Returns:
            Dictionary with total count and list of view models
        """
        try:
            models, total_count = self.service.get_deleted(
                db=db,
                skip=skip,
                limit=limit,
                include=include,
                filter_params=filter_params,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                select_fields=select_fields,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.get_deleted: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - {str(e)}")

        view_models = self.map_list_to_view(models, include, select_fields)
        return {"total": total_count, "data": view_models}

    async def hard_delete(
        self,
        db: Session,
        id: UUID
    ) -> Optional[Any]:
        """
        Hard delete an entity (permanently remove from database).

        Args:
            db: Database session
            id: Entity ID

        Returns:
            The deleted entity or None if not found
        """
        try:
            deleted_model = self.service.hard_delete(db=db, id=id)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Internal error in {self.entity_name}Service.hard_delete: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error - Hard Delete - {str(e)}")

        return deleted_model
