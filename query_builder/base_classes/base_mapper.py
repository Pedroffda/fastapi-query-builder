"""
Base Mapper for Query Builder Library

Provides common mapping operations with optimized relationship loading.
"""

import traceback
import logging
from typing import Generic, TypeVar, List, Optional, Dict, Any, Type, Set
from uuid import UUID
from enum import Enum
from sqlalchemy.inspection import inspect as sa_inspect

from ..core.select_parser import SelectParser
from ..exceptions.query_builder_exceptions import QueryBuilderException

logger = logging.getLogger(__name__)

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
ViewSchemaType = TypeVar('ViewSchemaType')  # Schema for returning an item


class BaseMapper(Generic[ModelType, ViewSchemaType]):
    """
    Base class for all Mapper classes to reduce code duplication and improve performance.

    This class provides common mapping operations with optimized relationship loading.
    """

    def __init__(
        self,
        model_class: Type[ModelType],
        view_class: Type[ViewSchemaType],
        entity_name: str,
        relationship_map: Dict[str, Dict[str, Any]]
    ):
        """
        Initialize the base mapper with model class, view class, and relationship map.

        Args:
            model_class: The SQLAlchemy model class
            view_class: The Pydantic view model class
            entity_name: The name of the entity (used in error messages)
            relationship_map: Dictionary mapping relationship names to their mapper functions and types
                Format: {
                    'relation_name': {
                        'mapper': mapper_function,
                        'is_list': True/False,
                        'model_class': RelatedModelClass
                    }
                }
        """
        self.model_class = model_class
        self.view_class = view_class
        self.entity_name = entity_name
        self.relationship_map = relationship_map
        self._visiting_tracker: Set[UUID] = set()
        self.select_parser = SelectParser()

    def _is_being_visited(self, model: ModelType) -> bool:
        """Check if a model is already being visited to prevent infinite recursion."""
        model_id = getattr(model, 'id', None)
        if model_id is None:
            return False

        return model_id in self._visiting_tracker

    def _mark_as_visiting(self, model: ModelType) -> None:
        """Mark a model as being visited."""
        model_id = getattr(model, 'id', None)
        if model_id is not None:
            self._visiting_tracker.add(model_id)

    def _unmark_as_visiting(self, model: ModelType) -> None:
        """Unmark a model as being visited."""
        model_id = getattr(model, 'id', None)
        if model_id is not None and model_id in self._visiting_tracker:
            self._visiting_tracker.remove(model_id)

    def _handle_enum_value(self, value: Any) -> Any:
        """Convert enum values to their string representation."""
        if isinstance(value, Enum):
            return value.value
        return value

    def _extract_model_data(self, model: ModelType) -> Dict[str, Any]:
        """Extract data from a model instance."""
        data = {}
        for column in model.__table__.columns:
            attr_name = column.name
            value = getattr(model, attr_name, None)
            data[attr_name] = self._handle_enum_value(value)

        return data

    def map_to_view(
        self,
        model: ModelType,
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
        _is_top_level_call: Optional[bool] = True,
    ) -> Optional[ViewSchemaType]:
        """
        Map a model instance to a view model.

        Args:
            model: The model instance to map
            include: List of relationships to include
            select_fields: Fields to select for serialization
            _is_top_level_call: Whether this is a top-level call (for select_fields handling)

        Returns:
            The mapped view model or None if mapping fails
        """
        if model is None:
            return None

        # Check for circular references
        if self._is_being_visited(model):
            return None

        # Mark as visiting to prevent infinite recursion
        self._mark_as_visiting(model)

        try:
            # Extract base data from model
            view_data = self._extract_model_data(model)

            # Initialize relationship fields
            for rel_name, rel_config in self.relationship_map.items():
                if rel_config.get('is_list', False):
                    view_data[rel_name] = []
                else:
                    view_data[rel_name] = None

            # Determine which relationships to include
            requested_rels: List[str] = list(include or [])

            if select_fields:
                model_relation_keys = {r.key for r in sa_inspect(self.model_class).relationships}
                requested_rels.extend(
                    list(
                        self.select_parser.extract_relationships_from_select_hybrid(select_fields, model_relation_keys)
                    )
                )

            if requested_rels:
                for rel_name in requested_rels:
                    if rel_name in self.relationship_map:
                        rel_config = self.relationship_map[rel_name]
                        mapper_func = rel_config.get('mapper')

                        if mapper_func:
                            related_attr = getattr(model, rel_name, None)

                            # Derive select_fields specific to this nested relation
                            nested_select_fields: Optional[str] = None
                            if select_fields:
                                raw_fields = [f.strip() for f in select_fields.split(',') if f.strip()]

                                # Fields that belong to this relationship (ex: "medico.usuario.id" -> "usuario.id")
                                nested_parts = []
                                prefix_dot = f"{rel_name}."
                                bracket_prefix = f"[{rel_name}]"

                                for field_path in raw_fields:
                                    if field_path.startswith(prefix_dot):
                                        nested_parts.append(field_path[len(prefix_dot):])
                                    elif field_path.startswith(bracket_prefix):
                                        trimmed = field_path[len(bracket_prefix):]
                                        if trimmed.startswith('.'):
                                            trimmed = trimmed[1:]
                                        nested_parts.append(trimmed)

                                if nested_parts:
                                    nested_select_fields = ','.join(nested_parts)

                            def _safe_call(mapper_fn, *args):
                                """Call mapper_fn trying to pass select_fields if supported."""
                                try:
                                    return mapper_fn(*args, nested_select_fields)
                                except TypeError:
                                    # Mapper doesn't accept select_fields
                                    return mapper_fn(*args)

                            if related_attr is not None:
                                if rel_config.get('is_list', False):
                                    # Handle to-many relationships
                                    if isinstance(related_attr, (list, set)):
                                        mapped_list = [_safe_call(mapper_func, obj, include) for obj in related_attr if obj is not None]
                                        view_data[rel_name] = [item for item in mapped_list if item is not None]
                                else:
                                    # Handle to-one relationships
                                    mapped_related = _safe_call(mapper_func, related_attr, include)
                                    if mapped_related:
                                        view_data[rel_name] = mapped_related

            # Validate and create view model
            try:
                validated_view = self.view_class.model_validate(view_data)
                result_object = validated_view
            except Exception as e_pydantic:
                logger.error(f"Pydantic validation failed for {self.entity_name}View ID {getattr(model, 'id', None)}. Error: {e_pydantic}")
                if select_fields:
                    try:
                        # Fallback to construct partial object for parent validation
                        partial_obj = self.view_class.model_construct(**view_data)
                        result_object = partial_obj
                    except Exception as e_fallback:
                        logger.error(f"Failed to apply partial dict fallback for {self.entity_name}: {e_fallback}")
                        return None
                else:
                    return None
                
            if select_fields and _is_top_level_call:
                include_structure = self.select_parser.parse_select_fields_for_pydantic(select_fields)
                return result_object.model_dump(include=include_structure)

            # If it's a nested call or doesn't have select_fields, return the Pydantic object
            return result_object

        except Exception as e_outer:
            logger.error(f"Unexpected error in mapper for {self.entity_name} (ID: {getattr(model, 'id', None)}). Error: {e_outer}")
            logger.debug(traceback.format_exc())
            return None
        finally:
            # Unmark as visiting
            self._unmark_as_visiting(model)

    def map_list_to_view(
        self,
        models: List[ModelType],
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
        _is_top_level_call: bool = True,
    ) -> List[ViewSchemaType]:
        """
        Map a list of model instances to view models.

        Args:
            models: The list of model instances to map
            include: List of relationships to include
            select_fields: Fields to select for serialization
            _is_top_level_call: Whether this is a top-level call

        Returns:
            The list of mapped view models
        """
        if not models:
            return []

        mapped_list = [self.map_to_view(model, include, select_fields, _is_top_level_call) for model in models if model is not None]
        return [view for view in mapped_list if view is not None]
