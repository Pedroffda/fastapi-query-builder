# FastAPI Query Builder - Usage Guide

## 🎯 New Installation Model (Like shadcn/ui)

The FastAPI Query Builder now follows the shadcn/ui model, giving you full control over the code.

## Installation & Setup

### 1. Install the Package

```bash
pip install fastapi-query-builder
```

### 2. Initialize in Your Project

```bash
# Initialize in your current project
query-builder init

# Or specify a custom directory
query-builder init --dir my_query_builder
```

This creates a local `query_builder/` directory with all the source code that you can modify.

### 3. Use in Your Code

```python
# Import from your local copy
from query_builder import QueryBuilder, BaseService, BaseMapper, BaseUseCase
```

## Project Structure After Initialization

```
your-project/
├── query_builder/           # Your local copy (customizable!)
│   ├── core/               # Core parsers
│   │   ├── filter_parser.py
│   │   ├── sort_parser.py
│   │   ├── search_parser.py
│   │   ├── select_parser.py
│   │   └── query_builder.py
│   ├── base_classes/       # Base classes
│   │   ├── base_service.py
│   │   ├── base_mapper.py
│   │   └── base_use_case.py
│   ├── utils/              # Utilities
│   ├── exceptions/         # Custom exceptions
│   ├── examples/           # Usage examples
│   └── example_usage.py    # Generated example
├── your_app/
└── requirements.txt
```

## Customization Examples

### 1. Add New Filter Operators

Edit `query_builder/core/filter_parser.py`:

```python
OPERATOR_MAP = {
    # ... existing operators ...
    'regex': lambda c, v: c.op('~')(v),  # PostgreSQL regex
    'date_range': lambda c, v: c.between(v[0], v[1]),  # Date range
    'json_contains': lambda c, v: c.op('?')(v),  # JSON contains
}
```

### 2. Custom Service Logic

Edit `query_builder/base_classes/base_service.py`:

```python
class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, GenericSchemaType]):
    # ... existing code ...
    
    def get_by_custom_field(self, db: Session, field_value: str):
        """Custom method for your specific needs"""
        query = select(self.model_class).where(
            self.model_class.custom_field == field_value,
            self.model_class.flg_excluido == False
        )
        return db.execute(query).scalar_one_or_none()
```

### 3. Custom Mapper Logic

Edit `query_builder/base_classes/base_mapper.py`:

```python
def map_to_view(self, model, include=None, select_fields=None, _is_top_level_call=True):
    # ... existing code ...
    
    # Add your custom mapping logic
    if hasattr(model, 'custom_field'):
        view_data['custom_computed_field'] = self._compute_custom_field(model)
    
    return result_object

def _compute_custom_field(self, model):
    """Your custom computation logic"""
    return f"{model.name}_{model.id}"
```

### 4. Add New Utilities

Create `query_builder/utils/custom_utils.py`:

```python
def custom_date_formatter(date_obj):
    """Custom date formatting utility"""
    return date_obj.strftime("%Y-%m-%d %H:%M:%S")

def custom_validation(data):
    """Custom validation logic"""
    # Your validation code here
    return True
```

## Updating Your Local Copy

When a new version is released:

```bash
# Update the package
pip install --upgrade fastapi-query-builder

# Update your local copy (preserves customizations)
query-builder update
```

The update process:
1. Backs up your custom files (files matching `custom_*.py`, `*_custom.py`, etc.)
2. Updates the core library files
3. Restores your customizations

## CLI Commands

```bash
# Initialize query_builder in your project
query-builder init

# Initialize in a custom directory
query-builder init --dir my_custom_query_builder

# Update your local installation
query-builder update

# Get help
query-builder --help
```

## Best Practices

### 1. File Naming for Customizations

Use these patterns for files you want to preserve during updates:
- `custom_*.py`
- `*_custom.py`
- `my_*.py`
- `local_*.py`

### 2. Extending vs Modifying

**Prefer extending over modifying:**

```python
# Good: Extend the base class
class MyCustomService(BaseService):
    def get_by_custom_field(self, db: Session, field_value: str):
        # Your custom logic
        pass

# Avoid: Modifying the base class directly
# (Your changes will be lost on updates)
```

### 3. Version Control

Commit your `query_builder/` directory to version control:

```bash
git add query_builder/
git commit -m "Add FastAPI Query Builder with customizations"
```

### 4. Team Collaboration

When working in a team:
1. Everyone runs `query-builder init` to get the base code
2. Share customizations through version control
3. Use `query-builder update` to get new versions
4. Merge customizations as needed

## Migration from Direct Import

If you were using the direct import method:

```python
# Old way
from query_builder import QueryBuilder

# New way (after init)
from query_builder import QueryBuilder  # Same import, but from local copy
```

The API remains the same, but now you have the source code locally.

## Troubleshooting

### Issue: CLI command not found

```bash
# Make sure the package is installed
pip install fastapi-query-builder

# Check if the command is available
which query-builder
```

### Issue: Import errors after init

```bash
# Make sure you're in the right directory
pwd

# Check if query_builder directory exists
ls -la query_builder/
```

### Issue: Update doesn't preserve customizations

Make sure your custom files follow the naming patterns:
- `custom_*.py`
- `*_custom.py`
- `my_*.py`
- `local_*.py`

## Examples

Check the `query_builder/examples/` directory for complete usage examples.

## Support

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Community questions
- Documentation: Check the examples/ directory
