"""
Query Builder Library

A library for building SQLAlchemy queries with support for:
- Advanced filtering with operators
- Sorting
- Text search
- Field and relationship selection
- Pagination
- Model to Pydantic schema mapping

Usage example:
    from lib.query_builder import QueryBuilder, BaseService, BaseMapper, BaseUseCase
    
    # Configure service
    service = BaseService(Model, "entity_name", relationship_map, schema_class)
    
    # Configure mapper
    mapper = BaseMapper(Model, ViewSchema, "entity_name", relationship_map)
    
    # Configure use case
    use_case = BaseUseCase(service, "entity_name", mapper.map_to_view, mapper.map_list_to_view)
"""

from .core.query_builder import QueryBuilder
from .core.filter_parser import FilterParser
from .core.sort_parser import SortParser
from .core.search_parser import SearchParser
from .core.select_parser import SelectParser
from .base_classes.base_service import BaseService
from .base_classes.base_mapper import BaseMapper
from .base_classes.base_use_case import BaseUseCase
from .utils.relationship_utils import get_dynamic_relations_map
from .exceptions.query_builder_exceptions import (
    QueryBuilderException,
    InvalidFilterException,
    InvalidSortException,
    InvalidSelectException,
    RelationshipNotFoundException
)

__version__ = "1.0.0"
__author__ = "Pedro"

__all__ = [
    # Core classes
    "QueryBuilder",
    "FilterParser", 
    "SortParser",
    "SearchParser",
    "SelectParser",
    
    # Base classes
    "BaseService",
    "BaseMapper", 
    "BaseUseCase",
    
    # Utilities
    "get_dynamic_relations_map",
    
    # Exceptions
    "QueryBuilderException",
    "InvalidFilterException",
    "InvalidSortException", 
    "InvalidSelectException",
    "RelationshipNotFoundException"
]
