"""
Sort Parser for Query Builder Library

Handles parsing and applying sorting to SQLAlchemy queries.
"""

import logging
from typing import Optional, Dict, Any, Type, Literal
from sqlalchemy.sql.selectable import Select
from sqlalchemy import asc, desc
from sqlalchemy.orm import RelationshipProperty

from ..exceptions.query_builder_exceptions import InvalidSortException

logger = logging.getLogger(__name__)


class SortParser:
    """Parser for handling sort operations on SQLAlchemy queries"""
    
    def apply_sorting(
        self,
        query: Select,
        model_cls: Type,
        sort_by: str,
        sort_dir: Optional[Literal["asc", "desc"]],
        relations_map: Dict[str, RelationshipProperty]
    ) -> Select:
        """Apply sorting to SQLAlchemy query"""
        if not sort_by:
            return query

        direction = sort_dir.lower() if sort_dir else "asc"
        if direction not in ("asc", "desc"):
            raise InvalidSortException(f"Direção de ordenação inválida: '{sort_dir}'. Use 'asc' ou 'desc'.")

        try:
            # Import here to avoid circular imports
            from .filter_parser import FilterParser
            filter_parser = FilterParser()
            target_column, _, joins_to_apply = filter_parser._get_column_or_relationship(
                model_cls, sort_by, relations_map
            )
        except Exception as e:
            logger.error(f"Erro ao processar ordenação por '{sort_by}': {e}")
            raise InvalidSortException(f"Erro ao processar ordenação por '{sort_by}': {e}")

        # Apply JOINs for sorting
        for rel_prop in joins_to_apply:
            logger.debug(f"Garantindo JOIN para ordenação na relação: {rel_prop} (originado por sort_by='{sort_by}')")
            query = query.join(rel_prop.class_attribute, isouter=True)

        order_func = asc if direction == "asc" else desc
        query = query.order_by(order_func(target_column))
        logger.debug(f"Aplicando ordenação: {order_func(target_column)}")

        return query
