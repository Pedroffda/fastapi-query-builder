"""
Filter Parser for Query Builder Library

Handles parsing and applying filters to SQLAlchemy queries.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Type, Tuple, Set
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import with_loader_criteria

from ..exceptions.query_builder_exceptions import InvalidFilterException

logger = logging.getLogger(__name__)

FILTER_PATTERN = re.compile(r"filter\[(.+?)\]\[(.+?)\]")

OPERATOR_MAP = {
    'eq': lambda c, v: c == v,
    'neq': lambda c, v: c != v,
    'lt': lambda c, v: c < v,
    'lte': lambda c, v: c <= v,
    'gt': lambda c, v: c > v,
    'gte': lambda c, v: c >= v,
    'in': lambda c, v: c.in_(v),
    'notin': lambda c, v: c.notin_(v),
    'like': lambda c, v: c.like(v),
    'ilike': lambda c, v: c.ilike(v),
    # 'isnull': lambda c, v: c.is_(None) if self._parse_bool(v) else c.is_not(None),
    'contains': lambda c, v: c.contains(v),
    'startswith': lambda c, v: c.startswith(v),
    'endswith': lambda c, v: c.endswith(v),
}


class FilterParser:
    """Parser for handling filter operations on SQLAlchemy queries"""
    
    def __init__(self):
        self.already_joined_relationships_for_where: Set[RelationshipProperty] = set()
        self.applied_loader_criteria_options: Set[tuple] = set()
    
    def _parse_bool(self, value: Any) -> bool:
        """Convert a value to boolean flexibly."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        return bool(value)

    def _parse_filter_value(self, value: str) -> Any:
        """Parse filter value with type conversion"""
        value_lower = value.lower()
        if value_lower in ('true', 'yes', 'on', '1'):
            return True
        if value_lower in ('false', 'no', 'off', '0'):
            return False
        if value_lower in ('null', 'none'):
            return None
        return value

    def _get_column_or_relationship(
        self,
        model_cls: Type,
        field_specifier: str,
        relations_map: Dict[str, RelationshipProperty]
    ) -> Tuple[InstrumentedAttribute, Optional[Type], List[RelationshipProperty]]:
        """Get column or relationship attribute from field specifier"""
        parts = field_specifier.split('.')
        current_model = model_cls
        target_attribute = None
        joins_needed: List[RelationshipProperty] = []

        for i, part in enumerate(parts):
            if not hasattr(current_model, part):
                raise InvalidFilterException(
                    f"Modelo '{current_model.__name__}' não possui o atributo ou relação '{part}' especificado em '{field_specifier}'"
                )

            attr = getattr(current_model, part)

            if isinstance(attr.property, RelationshipProperty):
                if i == len(parts) - 1:
                    raise InvalidFilterException(
                        f"Não é possível filtrar/ordenar diretamente pela relação '{part}'. Especifique um campo dentro dela (ex: '{field_specifier}.id')."
                    )

                current_relationship_prop: RelationshipProperty = attr.property

                if i == 0:
                    if part not in relations_map:
                        raise InvalidFilterException(
                            f"Relação '{part}' não encontrada no 'relations_map' fornecido para o modelo base {model_cls.__name__}. Certifique-se que o relations_map contém '{part}': Model.{part}.property."
                        )
                    joins_needed.append(relations_map[part])
                else:
                    joins_needed.append(current_relationship_prop)

                current_model = current_relationship_prop.mapper.class_
            elif isinstance(attr, InstrumentedAttribute):
                if i != len(parts) - 1:
                    raise InvalidFilterException(
                        f"Atributo '{part}' em '{field_specifier}' não é uma relação, mas existem mais partes."
                    )
                target_attribute = attr
                break
            else:
                raise InvalidFilterException(
                    f"Atributo '{part}' em '{field_specifier}' tem tipo inesperado: {type(attr)}. Esperado InstrumentedAttribute."
                )

        if target_attribute is None:
            raise InvalidFilterException(
                f"Não foi possível resolver o atributo final para '{field_specifier}'."
            )

        return target_attribute, current_model, joins_needed

    def parse_filters(self, query_params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Parse filter parameters from query params"""
        filters: Dict[str, Dict[str, Any]] = {}
        processed_keys = set()

        logger.debug(f"Parsing query params: {query_params}")

        for key, value in query_params.items():
            if key in processed_keys:
                continue

            match = FILTER_PATTERN.fullmatch(key)
            if match:
                field_specifier = match.group(1)
                operator = match.group(2).lower()

                if not field_specifier or not operator:
                    logger.warning(f"Ignorando filtro com field ou operator vazio: {key}")
                    continue

                parsed_value = self._parse_filter_value(value)

                if field_specifier not in filters:
                    filters[field_specifier] = {}

                if operator in filters[field_specifier]:
                    logger.warning(
                        f"Sobrescrevendo filtro existente para {field_specifier}[{operator}] com valor '{value}'. Valor anterior era: {filters[field_specifier][operator]}"
                    )

                filters[field_specifier][operator] = parsed_value
                processed_keys.add(key)
                logger.debug(f"Parsed filter: field='{field_specifier}', operator='{operator}', value='{parsed_value}' (original: '{value}')")
            else:
                logger.debug(f"Ignorando parâmetro não-filtro: {key}")

        if not filters:
            logger.debug("Nenhum parâmetro de filtro encontrado.")
        else:
            logger.info(f"Filtros parseados: {filters}")

        return filters

    def apply_filters(
        self,
        query: Select,
        model_cls: Type,
        filter_params: Dict[str, Dict[str, Any]],
        relations_map: Dict[str, RelationshipProperty],
    ) -> Select:
        """Apply filters to SQLAlchemy query"""
        self.already_joined_relationships_for_where.clear()
        self.applied_loader_criteria_options.clear()

        for field_specifier, operators in filter_params.items():
            if not isinstance(operators, dict):
                logger.error(f"Valor para o filtro '{field_specifier}' não é um dicionário: {operators}")
                raise InvalidFilterException(f"Valor para o filtro '{field_specifier}' deve ser um dicionário de operadores.")

            try:
                target_column, _, joins_path_properties = self._get_column_or_relationship(
                    model_cls, field_specifier, relations_map
                )
            except InvalidFilterException as e:
                logger.error(f"Erro ao processar filtro para '{field_specifier}': {e}")
                raise

            # Apply JOINs for WHERE clause
            for i, rel_prop in enumerate(joins_path_properties):
                if rel_prop not in self.already_joined_relationships_for_where:
                    logger.debug(f"Aplicando JOIN para filtro WHERE na relação: {rel_prop} (de {field_specifier})")
                    query = query.join(rel_prop.class_attribute, isouter=True)
                    self.already_joined_relationships_for_where.add(rel_prop)

            for op_code, value in operators.items():
                op_func = OPERATOR_MAP.get(op_code.lower())
                if not op_func:
                    raise InvalidFilterException(
                        f"Operador de filtro inválido '{op_code}' para o campo '{field_specifier}'. Válidos: {list(OPERATOR_MAP.keys())}"
                    )

                try:
                    _original_value = value
                    if op_code.lower() in ('in', 'notin') and not isinstance(value, (list, tuple)):
                        if isinstance(value, str):
                            value = [item.strip() for item in value.split(',') if item.strip()]
                        else:
                            raise InvalidFilterException(
                                f"Valor para operador '{op_code}' no campo '{field_specifier}' deve ser uma lista/tupla ou string separada por vírgulas."
                            )

                    # Apply WHERE clause
                    filter_expression_for_where = op_func(target_column, value)
                    query = query.where(filter_expression_for_where)
                    logger.debug(f"Aplicando filtro WHERE: {filter_expression_for_where} para {field_specifier}")

                    # Apply with_loader_criteria for filtering loaded collections
                    if joins_path_properties:
                        first_relationship_property_in_path = joins_path_properties[0]
                        instrumented_relationship_on_model_cls = first_relationship_property_in_path.class_attribute

                        if target_column.parent.class_ == first_relationship_property_in_path.mapper.class_:
                            loader_criteria_expression = op_func(target_column, value)

                            option_key = (instrumented_relationship_on_model_cls.key, target_column.key, op_code, str(_original_value))
                            if option_key not in self.applied_loader_criteria_options:
                                query = query.options(
                                    with_loader_criteria(
                                        instrumented_relationship_on_model_cls,
                                        loader_criteria_expression
                                    )
                                )
                                self.applied_loader_criteria_options.add(option_key)
                                logger.debug(f"Aplicando with_loader_criteria para {instrumented_relationship_on_model_cls.key} com {loader_criteria_expression}")
                            else:
                                logger.debug(f"with_loader_criteria para {instrumented_relationship_on_model_cls.key} com {loader_criteria_expression} já aplicado.")
                        else:
                            logger.warning(
                                f"Filtragem de conteúdo de coleção aninhada profunda para '{field_specifier}' "
                                f"via with_loader_criteria não é automaticamente construída. "
                                f"O filtro principal será aplicado, mas a coleção '{instrumented_relationship_on_model_cls.key}' "
                                f"pode não ser filtrada profundamente se a condição estiver em uma sub-relação."
                            )

                except Exception as e:
                    logger.error(f"Erro ao aplicar operador '{op_code}' com valor '{value}' no campo '{field_specifier}': {e}")
                    raise InvalidFilterException(f"Erro ao aplicar filtro '{op_code}={value}' para '{field_specifier}': {e}") from e

        return query
