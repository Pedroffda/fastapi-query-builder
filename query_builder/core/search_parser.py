"""
Search Parser for Query Builder Library

Handles parsing and applying text search to SQLAlchemy queries.
"""

import logging
from typing import List, Optional, Type
from sqlalchemy.sql.selectable import Select
from sqlalchemy import inspect, or_

logger = logging.getLogger(__name__)


class SearchParser:
    """Parser for handling text search operations on SQLAlchemy queries"""
    
    def apply_search(
        self,
        query: Select,
        model_cls: Type,
        search: Optional[str],
        search_fields: List[str],
    ) -> Select:
        """Apply text search (case-insensitive) to specific fields, including relationship properties"""
        if not search or not search_fields:
            return query

        search_term = f"%{search}%"
        conditions = []
        mapper = inspect(model_cls)
        joins_added = set()

        for field_name in search_fields:
            # Check fields with dot notation (ex: 'voucher.codigo_voucher')
            if '.' in field_name:
                rel_name, rel_field = field_name.split('.', 1)
                
                # Check if relationship exists
                if rel_name not in mapper.relationships:
                    logger.warning(f"Relacionamento '{rel_name}' não encontrado em {model_cls.__name__}")
                    continue
                    
                relationship = mapper.relationships[rel_name]
                if not hasattr(relationship, 'property'):
                    continue
                    
                # Add JOIN if needed
                if rel_name not in joins_added:
                    query = query.join(getattr(model_cls, rel_name))
                    joins_added.add(rel_name)
                
                # Get related model and check field
                related_model = relationship.mapper.class_
                related_mapper = inspect(related_model)
                
                if rel_field not in related_mapper.columns and rel_field not in related_mapper.synonyms:
                    logger.warning(f"Campo '{rel_field}' não encontrado em {related_model.__name__}")
                    continue
                    
                column = getattr(related_model, rel_field)
                if hasattr(column.type, "python_type") and issubclass(column.type.python_type, str):
                    conditions.append(column.ilike(search_term))
                else:
                    logger.warning(f"Campo '{field_name}' não é string, ignorando")
                    
            # Local field (non-relational)
            else:
                if field_name not in mapper.columns and field_name not in mapper.synonyms:
                    logger.warning(f"Campo local '{field_name}' não encontrado")
                    continue
                    
                column = getattr(model_cls, field_name)
                if hasattr(column.type, "python_type") and issubclass(column.type.python_type, str):
                    conditions.append(column.ilike(search_term))
                else:
                    logger.warning(f"Campo local '{field_name}' não é string, ignorando")

        if conditions:
            query = query.filter(or_(*conditions))
            logger.debug(f"Busca aplicada: termo='{search}' em campos={search_fields}")

        return query
