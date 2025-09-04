"""
Example of using the Query Builder Library

This example shows how to implement a complete CRUD for users
using the Query Builder library.
"""

from typing import List, Optional, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from starlette.datastructures import QueryParams

# Imports the library
from query_builder import (
    BaseService, 
    BaseMapper, 
    BaseUseCase, 
    QueryBuilder,
    get_dynamic_relations_map
)

# Imports your project (adjust as needed)
from your_models import User, Profile, Role  # Adjust the imports
from your_schemas import (
    UserCreate, 
    UserUpdate, 
    UserView,
    ProfileView,
    RoleView
)  # Adjust the imports
from your_database import get_db  # Adjust the import

# Configure the router
router = APIRouter(prefix="/users", tags=["users"])

# Instantiate the QueryBuilder
query_builder = QueryBuilder()

# ============================================================================
# CONFIGURATION OF THE RELATIONSHIP MAPPINGS
# ============================================================================

# Mapper for Profile
profile_mapper = BaseMapper(
    model_class=Profile,
    view_class=ProfileView,
    entity_name="profile",
    relationship_map={}  # Profile does not have relationships in this example
)

# Mapper for Role
role_mapper = BaseMapper(
    model_class=Role,
    view_class=RoleView,
    entity_name="role",
    relationship_map={}  # Role does not have relationships in this example
)

# Mapper for User
user_mapper = BaseMapper(
    model_class=User,
    view_class=UserView,
    entity_name="user",
    relationship_map={
        'profile': {
            'mapper': profile_mapper.map_to_view,
            'is_list': False,
            'model_class': Profile
        },
        'roles': {
            'mapper': role_mapper.map_to_view,
            'is_list': True,
            'model_class': Role
        }
    }
)

# ============================================================================
# CONFIGURATION OF THE SERVICE
# ============================================================================

# Get the dynamic relationship mapping
user_relationship_map = get_dynamic_relations_map(User)

# Configure the service
user_service = BaseService(
    model_class=User,
    entity_name="user",
    relationship_map=user_relationship_map,
    generic_schema=UserView,
    searchable_fields=[
        "name",
        "email",
        "profile.bio",  # Relationship field
        "roles.name"    # Nested field
    ],
    tenant_context_getter=lambda: get_current_tenant_id()  # Function to get the current tenant
)

# ============================================================================
# CONFIGURATION OF THE USE CASE
# ============================================================================

user_use_case = BaseUseCase(
    service=user_service,
    entity_name="user",
    map_to_view=user_mapper.map_to_view,
    map_list_to_view=user_mapper.map_list_to_view
)

# ============================================================================
# HELPER FUNCTION FOR TENANT
# ============================================================================

def get_current_tenant_id():
    """
    Function to get the current tenant.
    Adjust according to your implementation of multi-tenancy.
    """
    # Example: get from the request header
    # return request.headers.get("X-Tenant-ID")
    return "default-tenant"  # For the example

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/")
async def get_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query(None, description="Field to sort"),
    sort_dir: Optional[Literal["asc", "desc"]] = Query("asc", description="Direction of the sorting"),
    include: Optional[List[str]] = Query(None, description="Relationships to include"),
    select_fields: Optional[str] = Query(None, description="Fields to select"),
    query_params: QueryParams = Depends()
):
    """
    List users with filters, sorting, search and pagination.
    
    Examples of use:
    - GET /users?filter[name][eq]=John
    - GET /users?filter[age][gte]=18&filter[age][lt]=65
    - GET /users?search=John&sort_by=name&sort_dir=asc
    - GET /users?include=profile,roles&select=id,name,profile.bio
    """
    try:
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    include: Optional[List[str]] = Query(None, description="Relationships to include"),
    select_fields: Optional[str] = Query(None, description="Fields to select")
):
    """
    Get a specific user by ID.
    
    Examples of use:
    - GET /users/{id}
    - GET /users/{id}?include=profile,roles
    - GET /users/{id}?select=id,name,email,profile.bio
    """
    try:
        result = await user_use_case.get_by_id(
            db=db,
            id=user_id,
            include=include,
            select_fields=select_fields
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    """
    try:
        result = await user_use_case.create(db=db, data=user_data)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.put("/{user_id}")
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing user.
    """
    try:
        result = await user_use_case.update(db=db, id=user_id, data=user_data)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a user (soft delete).
    """
    try:
        result = await user_use_case.delete(db=db, id=user_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/{user_id}/restore")
async def restore_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Restore a deleted user (soft delete).
    """
    try:
        result = await user_use_case.restore(db=db, id=user_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/deleted/")
async def get_deleted_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query(None, description="Field to sort"),
    sort_dir: Optional[Literal["asc", "desc"]] = Query("asc", description="Direction of the sorting"),
    include: Optional[List[str]] = Query(None, description="Relationships to include"),
    select_fields: Optional[str] = Query(None, description="Fields to select"),
    query_params: QueryParams = Depends()
):
    """
    List deleted users (soft delete).
    """
    try:
        # Parse filters from query parameters
        filter_params = query_builder.parse_filters(query_params)
        
        # Get deleted users
        result = await user_use_case.get_deleted(
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.delete("/{user_id}/hard")
async def hard_delete_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a user permanently (hard delete).
    """
    try:
        result = await user_use_case.hard_delete(db=db, id=user_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted permanently"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ============================================================================
# EXAMPLES OF REQUESTS
# ============================================================================

"""
Examples of requests that can be made:

1. List all users:
   GET /users

2. Filter by name:
   GET /users?search=John

3. Filter by age:
   GET /users?filter[age][gte]=18&filter[age][lt]=65

4. Filter by email containing gmail:
   GET /users?filter[email][ilike]=@gmail.com

5. Sort by name:
   GET /users?sort_by=name&sort_dir=asc

6. Include relationships:
   GET /users?include=profile,roles

7. Select specific fields:
   GET /users?select=id,name,email,profile.bio

8. Combination of filters:
   GET /users?filter[name][ilike]=John&filter[age][gte]=18&sort_by=name&include=profile

9. Pagination:
   GET /users?skip=20&limit=10

10. Search in relationship fields:
    GET /users?search=John&search_fields=name,profile.bio
"""
