"""
Relationship utilities for Query Builder Library
"""

import logging
from typing import Dict, Type
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import RelationshipProperty

logger = logging.getLogger(__name__)


def get_dynamic_relations_map(model_cls: Type) -> Dict[str, RelationshipProperty]:
    """
    Generate the relations_map dynamically for a model.
    
    Args:
        model_cls: The SQLAlchemy model class
        
    Returns:
        Dictionary mapping relationship names to RelationshipProperty objects
    """
    mapper = sa_inspect(model_cls)
    return {
        rel.key: rel.property  # rel is InspectionAttr, rel.property is the RelationshipProperty
        for rel in mapper.relationships
    }
