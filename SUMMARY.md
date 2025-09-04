# Query Builder Library - Resumo

## 📁 Estrutura da Biblioteca

```
lib/query_builder/
├── 📁 core/                    # Componentes principais
│   ├── filter_parser.py        # Parser de filtros
│   ├── sort_parser.py          # Parser de ordenação
│   ├── search_parser.py        # Parser de busca
│   ├── select_parser.py        # Parser de seleção
│   └── query_builder.py        # Orquestrador principal
├── 📁 base_classes/            # Classes base
│   ├── base_service.py         # Service base
│   ├── base_mapper.py          # Mapper base
│   └── base_use_case.py        # Use case base
├── 📁 utils/                   # Utilitários
│   └── relationship_utils.py   # Utilitários de relacionamento
├── 📁 exceptions/              # Exceções customizadas
│   └── query_builder_exceptions.py
├── 📁 examples/                # Exemplos de uso
│   └── user_example.py         # Exemplo completo
├── 📁 tests/                   # Testes
│   └── test_filter_parser.py   # Testes básicos
├── README.md                   # Documentação principal
├── MIGRATION_GUIDE.md          # Guia de migração
├── pyproject.toml              # Configuração do projeto
└── setup.py                    # Setup para instalação
```

## 🚀 Funcionalidades

### ✅ Filtragem Avançada
- **Operadores**: eq, neq, lt, lte, gt, gte, in, notin, like, ilike, isnull, contains, startswith, endswith
- **Relacionamentos**: Filtros em campos de tabelas relacionadas
- **Sintaxe**: `filter[campo][operador]=valor`

### ✅ Ordenação
- **Campos locais**: Ordenação por qualquer campo do modelo
- **Relacionamentos**: Ordenação por campos de tabelas relacionadas
- **Direções**: asc, desc

### ✅ Busca Textual
- **Case-insensitive**: Busca sem distinção de maiúsculas/minúsculas
- **Múltiplos campos**: Busca em vários campos simultaneamente
- **Relacionamentos**: Busca em campos de tabelas relacionadas

### ✅ Seleção de Campos
- **Campos simples**: `select=id,name,email`
- **Relacionamentos**: `select=[profile],[roles]`
- **Campos aninhados**: `select=profile.bio,roles.name`
- **Sintaxe híbrida**: `select=id,name,profile.bio,[roles].name`

### ✅ Paginação
- **Skip/Limit**: Controle de paginação
- **Contagem total**: Retorna total de registros

### ✅ Mapeamento
- **SQLAlchemy → Pydantic**: Mapeamento automático
- **Relacionamentos**: Mapeamento de relacionamentos aninhados
- **Seleção parcial**: Suporte a seleção de campos específicos

### ✅ Multi-tenant
- **Filtro automático**: Filtro por tenant_id automático
- **Contexto**: Suporte a contexto de tenant

### ✅ Soft Delete
- **Exclusão lógica**: Suporte nativo a soft delete
- **Restauração**: Restauração de registros excluídos
- **Hard delete**: Exclusão permanente

## 📋 Exemplo de Uso

### 1. Configuração Básica
```python
from lib.query_builder import BaseService, BaseMapper, BaseUseCase, get_dynamic_relations_map

# Service
relationship_map = get_dynamic_relations_map(User)
user_service = BaseService(
    model_class=User,
    entity_name="user",
    relationship_map=relationship_map,
    generic_schema=UserView,
    searchable_fields=["name", "email", "profile.bio"]
)

# Mapper
user_mapper = BaseMapper(
    model_class=User,
    view_class=UserView,
    entity_name="user",
    relationship_map={
        'profile': {
            'mapper': profile_mapper.map_to_view,
            'is_list': False,
            'model_class': Profile
        }
    }
)

# Use Case
user_use_case = BaseUseCase(
    service=user_service,
    entity_name="user",
    map_to_view=user_mapper.map_to_view,
    map_list_to_view=user_mapper.map_list_to_view
)
```

### 2. Endpoint
```python
from lib.query_builder import QueryBuilder

query_builder = QueryBuilder()

@router.get("/users")
async def get_users(
    query_params: QueryParams = Depends(),
    skip: int = Query(0),
    limit: int = Query(100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[Literal["asc", "desc"]] = Query("asc"),
    include: Optional[List[str]] = Query(None),
    select_fields: Optional[str] = Query(None)
):
    filter_params = query_builder.parse_filters(query_params)
    
    result = await user_use_case.get_all(
        db=db,
        skip=skip,
        limit=limit,
        include=include,
        filter_params=filter_params,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        select_fields=select_fields
    )
    
    return result
```

## 🔧 Migração

### Antes
```python
from api.utils.utils_bd import parse_filters, apply_filters, apply_sorting
from api.v1._shared.base_service import BaseService
```

### Depois
```python
from lib.query_builder import QueryBuilder, BaseService
```

## 📚 Documentação

- **README.md**: Documentação completa com exemplos
- **MIGRATION_GUIDE.md**: Guia detalhado de migração
- **examples/**: Exemplos práticos de implementação
- **tests/**: Testes básicos da biblioteca

## 🎯 Benefícios

1. **Organização**: Código separado em módulos especializados
2. **Reutilização**: Biblioteca pode ser usada em outros projetos
3. **Extensibilidade**: Fácil adicionar novos parsers e funcionalidades
4. **Manutenibilidade**: Código mais limpo e organizado
5. **Testabilidade**: Componentes independentes e testáveis
6. **Documentação**: Documentação completa e exemplos práticos

## 🚀 Próximos Passos

1. **Migrar código existente** usando o MIGRATION_GUIDE.md
2. **Testar funcionalidades** com os exemplos fornecidos
3. **Personalizar** conforme necessidades específicas
4. **Estender** com novos parsers ou funcionalidades
5. **Contribuir** com melhorias e correções

## 📞 Suporte

- Consulte o README.md para documentação completa
- Use o MIGRATION_GUIDE.md para migração
- Verifique os exemplos em examples/
- Execute os testes em tests/
