# FastAPI Query Builder

A library for building SQLAlchemy queries with support for advanced filtering, sorting, text search, field and relationship selection, pagination, and model to Pydantic schema mapping.

## Features

- **Advanced Filtering**: Support for multiple operators (eq, neq, lt, lte, gt, gte, in, notin, like, ilike, isnull, contains, startswith, endswith)
- **Sorting**: Sorting by local fields and relationships
- **Text Search**: Case-insensitive search in specific fields
- **Field Selection**: Granular control of which fields and relationships to load
- **Pagination**: Native pagination support
- **Mapping**: Automatic mapping between SQLAlchemy models and Pydantic schemas
- **Multi-tenant**: Automatic tenant filtering support
- **Soft Delete**: Native soft delete support
- **Customizable**: Install and modify the code locally like shadcn/ui

## Installation

### Option 1: Install and Initialize (Recommended)

This approach gives you full control over the code, similar to shadcn/ui:

```bash
# Install the package
pip install fastapi-sqlalchemy-query-builder

# Initialize in your project (creates a local copy you can modify)
query-builder init
```

This will create a `query_builder/` directory in your project with all the source code that you can customize as needed.

### Option 2: Direct Import

```bash
pip install fastapi-sqlalchemy-query-builder
```

Then import directly:

```python
from query_builder import QueryBuilder, BaseService, BaseMapper, BaseUseCase
```

## Usage

### With Local Installation (Recommended)

After running `query-builder init`, you'll have a local `query_builder/` directory:

```python
# Import from your local copy
from query_builder import QueryBuilder, BaseService, BaseMapper, BaseUseCase
from your_models import User
from your_schemas import UserCreate, UserUpdate, UserView

# Get relationship mapping dynamically
from query_builder.utils import get_dynamic_relations_map
relationship_map = get_dynamic_relations_map(User)

# Configure the service
user_service = BaseService(
    model_class=User,
    entity_name="user",
    relationship_map=relationship_map,
    generic_schema=UserView,
    searchable_fields=["name", "email", "profile.bio"]
)

# Configure the mapper
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

# Configure the use case
user_use_case = BaseUseCase(
    service=user_service,
    entity_name="user",
    map_to_view=user_mapper.map_to_view,
    map_list_to_view=user_mapper.map_list_to_view
)
```

### CLI Commands

```bash
# Initialize query_builder in your project
query-builder init

# Initialize in a custom directory
query-builder init --dir my_query_builder

# Update your local installation (preserves custom files)
query-builder update
```

### Example Endpoint

```python
from fastapi import APIRouter, Depends, Query
from starlette.datastructures import QueryParams
from query_builder import QueryBuilder

router = APIRouter()
query_builder = QueryBuilder()

@router.get("/users")
async def get_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[Literal["asc", "desc"]] = Query("asc"),
    include: Optional[List[str]] = Query(None),
    select_fields: Optional[str] = Query(None),
    query_params: QueryParams = Depends()
):
    # Parse filters from query parameters
    filter_params = query_builder.parse_filters(query_params)
    
    # Get users with all operations
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

## Filter Syntax

### Supported Operators

- `eq`: Equal to
- `neq`: Not equal to
- `lt`: Less than
- `lte`: Less than or equal to
- `gt`: Greater than
- `gte`: Greater than or equal to
- `in`: Is in (list)
- `notin`: Is not in (list)
- `like`: Contains (case-sensitive)
- `ilike`: Contains (case-insensitive)
- `isnull`: Is null (true/false)
- `contains`: Contains substring
- `startswith`: Starts with
- `endswith`: Ends with

### Filter Examples

```
GET /users?filter[name][eq]=John
GET /users?filter[age][gte]=18&filter[age][lt]=65
GET /users?filter[email][ilike]=@gmail.com
GET /users?filter[status][in]=active,inactive
GET /users?filter[profile.bio][contains]=developer
```

## Selection Syntax

### Simple Fields
```
GET /users?select=id,name,email
```

### Relationships
```
GET /users?select=id,name,[profile],[roles]
```

### Nested Fields
```
GET /users?select=id,name,profile.bio,roles.name
```

### Hybrid Syntax
```
GET /users?select=id,name,profile.bio,[roles].name
```

## Customization

Since you have the source code locally, you can:

1. **Modify parsers** to add new operators
2. **Extend base classes** for custom functionality
3. **Add new utilities** for your specific needs
4. **Customize error handling** and messages
5. **Add new features** without waiting for upstream updates

### Example Customization

```python
# In your local query_builder/core/filter_parser.py
OPERATOR_MAP = {
    # ... existing operators ...
    'regex': lambda c, v: c.op('~')(v),  # Add regex support
    'date_range': lambda c, v: c.between(v[0], v[1]),  # Add date range
}
```

## Updating

When a new version is released:

```bash
# Update the package
pip install --upgrade fastapi-sqlalchemy-query-builder

# Update your local copy (preserves customizations)
query-builder update
```

The update command will:
- Backup your custom files
- Update the core library files
- Restore your customizations

## Project Structure

After initialization, your project will have:

```
your-project/
├── query_builder/           # Local copy (customizable)
│   ├── core/               # Core parsers
│   ├── base_classes/       # Base classes
│   ├── utils/              # Utilities
│   ├── exceptions/         # Custom exceptions
│   ├── examples/           # Usage examples
│   └── example_usage.py    # Generated example
├── your_app/
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Community questions
- Documentation: Check the examples/ directory
