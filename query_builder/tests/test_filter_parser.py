"""
Testes básicos para FilterParser
"""

from query_builder.core.filter_parser import FilterParser


class TestFilterParser:
    """Testes para FilterParser"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.parser = FilterParser()
    
    def test_parse_filter_value_boolean(self):
        """Testa parsing de valores booleanos"""
        assert self.parser._parse_filter_value("true") is True
        assert self.parser._parse_filter_value("false") is False
        assert self.parser._parse_filter_value("yes") is True
        assert self.parser._parse_filter_value("no") is False
        assert self.parser._parse_filter_value("1") is True
        assert self.parser._parse_filter_value("0") is False
    
    def test_parse_filter_value_null(self):
        """Testa parsing de valores nulos"""
        assert self.parser._parse_filter_value("null") is None
        assert self.parser._parse_filter_value("none") is None
    
    def test_parse_filter_value_string(self):
        """Testa parsing de strings"""
        assert self.parser._parse_filter_value("hello") == "hello"
        assert self.parser._parse_filter_value("123") == "123"
    
    def test_parse_filters_empty(self):
        """Testa parsing de filtros vazios"""
        result = self.parser.parse_filters({})
        assert result == {}
    
    def test_parse_filters_simple(self):
        """Testa parsing de filtros simples"""
        params = {
            "filter[name][eq]": "João",
            "filter[age][gte]": "18"
        }
        
        result = self.parser.parse_filters(params)
        
        assert "name" in result
        assert "age" in result
        assert result["name"]["eq"] == "João"
        assert result["age"]["gte"] == "18"
    
    def test_parse_filters_boolean(self):
        """Testa parsing de filtros booleanos"""
        params = {
            "filter[active][eq]": "true",
            "filter[deleted][eq]": "false"
        }
        
        result = self.parser.parse_filters(params)
        
        assert result["active"]["eq"] is True
        assert result["deleted"]["eq"] is False
    
    def test_parse_filters_ignore_non_filter(self):
        """Testa que parâmetros não-filtro são ignorados"""
        params = {
            "filter[name][eq]": "João",
            "skip": "10",
            "limit": "20",
            "sort_by": "name"
        }
        
        result = self.parser.parse_filters(params)
        
        assert "name" in result
        assert "skip" not in result
        assert "limit" not in result
        assert "sort_by" not in result
    
    def test_parse_filters_invalid_format(self):
        """Testa parsing de filtros com formato inválido"""
        params = {
            "filter[name]": "João",  # Sem operador
            "filter[][eq]": "João",  # Campo vazio
            "filter[name][]": "João"  # Operador vazio
        }
        
        result = self.parser.parse_filters(params)
        
        # Filtros inválidos devem ser ignorados
        assert result == {}
    
    def test_parse_filters_override(self):
        """Testa que filtros duplicados são sobrescritos"""
        params = {
            "filter[name][eq]": "João",
            "filter[name][eq]": "Maria"  # Deve sobrescrever o anterior
        }
        
        result = self.parser.parse_filters(params)
        
        assert result["name"]["eq"] == "Maria"
