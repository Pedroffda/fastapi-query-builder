"""
CLI tool for FastAPI Query Builder installation and customization
"""

import shutil
from pathlib import Path
from typing import Optional, List


class QueryBuilderCLI:
    """CLI tool for managing FastAPI Query Builder installations"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.query_builder_dir = self.project_root / "query_builder"
    
    def init(self, target_dir: Optional[str] = None):
        """Initialize query_builder in the current project"""
        if target_dir:
            self.query_builder_dir = self.project_root / target_dir
        
        if self.query_builder_dir.exists():
            print(f"❌ Directory {self.query_builder_dir} already exists!")
            return
        
        print(f"🚀 Initializing FastAPI Query Builder in {self.query_builder_dir}")
        
        # Get the source directory (where the package is installed)
        try:
            import query_builder
            source_dir = Path(query_builder.__file__).parent
        except ImportError:
            print("❌ FastAPI Query Builder not installed. Install it first:")
            print("   pip install fastapi-query-builder")
            return
        
        # Copy the source code
        shutil.copytree(source_dir, self.query_builder_dir)
        
        # Create a simple example
        self._create_example()
        
        print(f"✅ FastAPI Query Builder initialized in {self.query_builder_dir}")
        print("📝 You can now customize the code as needed!")
        print("📚 Check the examples/ directory for usage examples")
    
    def update(self):
        """Update the local query_builder installation"""
        if not self.query_builder_dir.exists():
            print(f"❌ No query_builder directory found in {self.project_root}")
            print("Run 'query-builder init' first")
            return
        
        print("🔄 Updating FastAPI Query Builder...")
        
        try:
            import query_builder
            source_dir = Path(query_builder.__file__).parent
        except ImportError:
            print("❌ FastAPI Query Builder not installed. Install it first:")
            print("   pip install fastapi-query-builder")
            return
        
        # Backup custom files
        custom_files = self._get_custom_files()
        backup_dir = self.query_builder_dir / ".backup"
        if custom_files:
            backup_dir.mkdir(exist_ok=True)
            for file_path in custom_files:
                backup_path = backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
            print(f"📦 Backed up {len(custom_files)} custom files")
        
        # Remove old installation
        shutil.rmtree(self.query_builder_dir)
        
        # Copy new version
        shutil.copytree(source_dir, self.query_builder_dir)
        
        # Restore custom files
        if custom_files and backup_dir.exists():
            for backup_file in backup_dir.glob("*"):
                target_file = self.query_builder_dir / backup_file.name
                if not target_file.exists():
                    shutil.copy2(backup_file, target_file)
            shutil.rmtree(backup_dir)
            print("🔄 Restored custom files")
        
        print("✅ FastAPI Query Builder updated successfully!")
    
    def _create_example(self):
        """Create a simple example file"""
        example_content = '''"""
Example usage of FastAPI Query Builder
"""

from query_builder import QueryBuilder, BaseService, BaseMapper, BaseUseCase
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional, List

# Example model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    age = Column(Integer)
    active = Column(Boolean, default=True)

# Example schemas
class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None

class UserView(BaseModel):
    id: int
    name: str
    email: str
    age: int
    active: bool

# Example usage
def example_usage():
    # Initialize query builder
    query_builder = QueryBuilder()
    
    # Example filter parsing
    filter_params = {
        "filter[name][eq]": "John",
        "filter[age][gte]": "18"
    }
    
    parsed_filters = query_builder.parse_filters(filter_params)
    print("Parsed filters:", parsed_filters)
    
    # Example select parsing
    select_fields = "id,name,email"
    parsed_select = query_builder.parse_select_fields_for_pydantic(select_fields)
    print("Parsed select:", parsed_select)

if __name__ == "__main__":
    example_usage()
'''
        
        example_file = self.query_builder_dir / "example_usage.py"
        with open(example_file, "w") as f:
            f.write(example_content)
    
    def _get_custom_files(self) -> List[Path]:
        """Get list of custom files that should be preserved during updates"""
        custom_files = []
        
        # Look for common custom file patterns
        custom_patterns = [
            "custom_*.py",
            "*_custom.py",
            "my_*.py",
            "local_*.py"
        ]
        
        for pattern in custom_patterns:
            custom_files.extend(self.query_builder_dir.glob(pattern))
        
        return custom_files


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FastAPI Query Builder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize query_builder in current project")
    init_parser.add_argument("--dir", help="Target directory (default: query_builder)")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update local query_builder installation")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = QueryBuilderCLI()
    
    if args.command == "init":
        cli.init(args.dir)
    elif args.command == "update":
        cli.update()


if __name__ == "__main__":
    main()
