"""
Custom exceptions for Query Builder Library
"""


class QueryBuilderException(Exception):
    """Base exception for Query Builder Library"""
    pass


class InvalidFilterException(QueryBuilderException):
    """Raised when filter parameters are invalid"""
    pass


class InvalidSortException(QueryBuilderException):
    """Raised when sort parameters are invalid"""
    pass


class InvalidSelectException(QueryBuilderException):
    """Raised when select parameters are invalid"""
    pass


class RelationshipNotFoundException(QueryBuilderException):
    """Raised when a relationship is not found in the model"""
    pass
