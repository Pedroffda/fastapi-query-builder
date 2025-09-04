"""
Main Query Builder for Query Builder Library

Orchestrates all parsing operations and provides a unified interface.
"""

import logging
from typing import List, Optional, Dict, Any, Type, Literal, Tuple
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import Session, RelationshipProperty
from starlette.datastructures import QueryParams

from .filter_parser import FilterParser
from .sort_parser import SortParser
from .search_parser import SearchParser
from .select_parser import SelectParser
from ..exceptions.query_builder_exceptions import QueryBuilderException

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Main query builder that orchestrates all parsing operations"""
    
    def __init__(self):
        self.filter_parser = FilterParser()
        self.sort_parser = SortParser()
        self.search_parser = SearchParser()
        self.select_parser = SelectParser()
    
    def parse_filters(self, query_params: QueryParams) -> Dict[str, Dict[str, Any]]:
        """Parse filter parameters from query params"""
        # Convert QueryParams to dict for easier handling
        params_dict = dict(query_params.multi_items())
        return self.filter_parser.parse_filters(params_dict)
    
    def apply_filters(
        self,
        query: Select,
        model_cls: Type,
        filter_params: Dict[str, Dict[str, Any]],
        relations_map: Dict[str, RelationshipProperty],
    ) -> Select:
        """Apply filters to SQLAlchemy query"""
        return self.filter_parser.apply_filters(query, model_cls, filter_params, relations_map)
    
    def apply_sorting(
        self,
        query: Select,
        model_cls: Type,
        sort_by: str,
        sort_dir: Optional[Literal["asc", "desc"]],
        relations_map: Dict[str, RelationshipProperty]
    ) -> Select:
        """Apply sorting to SQLAlchemy query"""
        return self.sort_parser.apply_sorting(query, model_cls, sort_by, sort_dir, relations_map)
    
    def apply_search(
        self,
        query: Select,
        model_cls: Type,
        search: Optional[str],
        search_fields: List[str],
    ) -> Select:
        """Apply text search to SQLAlchemy query"""
        return self.search_parser.apply_search(query, model_cls, search, search_fields)
    
    def apply_select_load_options(
        self,
        query: Select,
        model_cls: Type,
        include_param: Optional[str] = None,
    ) -> Select:
        """Apply select load options to SQLAlchemy query"""
        return self.select_parser.apply_select_load_options(query, model_cls, include_param)
    
    def parse_select_fields_for_pydantic(self, select_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse select fields for Pydantic model_dump"""
        return self.select_parser.parse_select_fields_for_pydantic(select_str)
    
    def extract_relationships_from_select_hybrid(
        self,
        select_param: Optional[str],
        model_relation_keys: set
    ) -> set:
        """Extract relationships from select parameter"""
        return self.select_parser.extract_relationships_from_select_hybrid(select_param, model_relation_keys)
    
    def build_query(
        self,
        base_query: Select,
        model_cls: Type,
        relations_map: Dict[str, RelationshipProperty],
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Dict[str, Any]]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[Literal["asc", "desc"]] = "asc",
        include_param: Optional[str] = None,
    ) -> Select:
        """
        Build a complete query with all operations applied
        
        Args:
            base_query: Base SQLAlchemy query
            model_cls: Model class
            relations_map: Relationship mapping
            search: Search term
            search_fields: Fields to search in
            filter_params: Filter parameters
            sort_by: Field to sort by
            sort_dir: Sort direction
            include_param: Include parameter for loading relationships
            
        Returns:
            Built query with all operations applied
        """
        query = base_query
        
        # Apply search
        if search and search_fields:
            query = self.apply_search(query, model_cls, search, search_fields)
        
        # Apply filters
        if filter_params:
            query = self.apply_filters(query, model_cls, filter_params, relations_map)
        
        # Apply sorting
        if sort_by:
            query = self.apply_sorting(query, model_cls, sort_by, sort_dir, relations_map)
        
        # Apply select load options
        if include_param:
            query = self.apply_select_load_options(query, model_cls, include_param)
        
        return query
