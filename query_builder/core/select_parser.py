"""
Select Parser for Query Builder Library

Handles parsing and applying field selection to SQLAlchemy queries.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Set, Type
from sqlalchemy.sql.selectable import Select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Load, selectinload, noload

from ..exceptions.query_builder_exceptions import InvalidSelectException

logger = logging.getLogger(__name__)


class SelectParser:
    """Parser for handling field selection operations on SQLAlchemy queries"""
    
    def parse_select_fields_for_pydantic(self, select_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Converte uma string de seleção (ex: "id,nome,curso.[categorias].id")
        em um dicionário para o argumento `include` do Pydantic model_dump,
        suportando aninhamento e sintaxe de lista `[...]` em qualquer nível.
        """
        if not select_str:
            return None

        fields_to_process: List[str] = [field.strip() for field in select_str.split(',') if field.strip()]
        if not fields_to_process:
            return None

        include_dict: Dict[str, Any] = {}
        
        list_part_regex = re.compile(r"\[([a-zA-Z0-9_]+)\]")

        for field_path in fields_to_process:
            parts = field_path.split('.')
            current_level = include_dict

            for i, part in enumerate(parts):
                is_last_part = (i == len(parts) - 1)
                
                list_match = list_part_regex.fullmatch(part)

                if list_match:
                    list_name = list_match.group(1)

                    if not isinstance(current_level.get(list_name), dict):
                        current_level[list_name] = {}
                    
                    list_container = current_level[list_name]

                    if not isinstance(list_container.get('__all__'), dict):
                         list_container['__all__'] = {}

                    if is_last_part:
                        list_container['__all__'] = True
                        break 
                    else:
                        current_level = list_container['__all__']

                else: 
                    if is_last_part:
                        if not isinstance(current_level.get(part), dict):
                            current_level[part] = True
                    else:
                        if not isinstance(current_level.get(part), dict):
                            current_level[part] = {}
                        current_level = current_level[part]

        logger.debug(f"Estrutura 'include' parseada para Pydantic: {include_dict}")
        return include_dict if include_dict else None

    def apply_select_load_options(
        self,
        query: Select,
        model_cls: Type,
        include_param: Optional[str] = None,
    ) -> Select:
        """
        Aplica opções de carregamento (selectinload, noload) à query SQLAlchemy
        com base no parâmetro 'include'.

        Por PADRÃO, relacionamentos NÃO são carregados para máxima performance.
        Apenas relacionamentos explicitamente mencionados no include são carregados.

        Args:
            include_param: String de include como "[tenants].nome,[roles].nome"

        Comportamento:
        - Sem include: todos relacionamentos são bloqueados (noload)
        - Com include: apenas relacionamentos especificados são carregados (selectinload)
        """
        model_inspector = sa_inspect(model_cls)
        model_relation_keys = {r.key for r in model_inspector.relationships}

        # Extract requested relationships
        relations_to_load = self.extract_relationships_from_select_hybrid(include_param, model_relation_keys)

        options_to_apply: List[Load] = []

        # Apply selectinload for requested relationships, noload for the rest
        for rel_name in model_relation_keys:
            rel_attr = getattr(model_cls, rel_name)

            if rel_name in relations_to_load:
                # Requested relationship: use selectinload
                options_to_apply.append(selectinload(rel_attr))
                logger.debug(f"Carregando relacionamento: {model_cls.__name__}.{rel_name}")
            else:
                # Non-requested relationship: use noload
                options_to_apply.append(noload(rel_attr))
                logger.debug(f"Bloqueando relacionamento: {model_cls.__name__}.{rel_name}")

        if options_to_apply:
            query = query.options(*options_to_apply)
            logger.debug(
                f"Aplicando {len(options_to_apply)} opções de carregamento para {model_cls.__name__}"
            )

        return query

    def extract_relationships_from_select_hybrid(
        self,
        select_param: Optional[str],
        model_relation_keys: Set[str]
    ) -> Set[str]:
        """
        Extrai nomes de relacionamentos da string 'select', suportando a nova sintaxe
        com colchetes `[relacao]` e a sintaxe antiga `relacao.campo`.

        Args:
            select_param: String como "[tenants].nome,roles.nome,id,email"
            model_relation_keys: Um set com os nomes das relações válidas no modelo.

        Returns:
            Set com os nomes dos relacionamentos: {"tenants", "roles"}
        """
        if not select_param:
            return set()

        relationships = set()
        raw_fields = [field.strip() for field in select_param.split(",") if field.strip()]

        for field_path in raw_fields:
            # New Syntax: [relation_name]...
            if field_path.startswith("[") and "]" in field_path:
                relation_match = re.match(r"\[([^\]]+)\]", field_path)
                if relation_match:
                    relationships.add(relation_match.group(1))
            else:
                # Old Syntax: relation_name.subfield
                base_name = field_path.split('.')[0]
                if base_name in model_relation_keys:
                    relationships.add(base_name)

        return relationships
