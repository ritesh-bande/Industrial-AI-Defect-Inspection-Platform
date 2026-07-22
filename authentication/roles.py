from fastapi import Depends, HTTPException, status
from typing import List
from models.models import User
from authentication.jwt import get_current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Validates that the user's role matches the allowable route permissions.
        """
        # Admin bypass
        if current_user.role == "admin":
            return current_user
            
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' has insufficient permissions. Required: {self.allowed_roles}",
            )
        return current_user

# Predefined role dependencies
require_admin = RoleChecker(["admin"])
require_quality_manager = RoleChecker(["admin", "quality_manager"])
require_supervisor = RoleChecker(["admin", "quality_manager", "factory_supervisor"])
require_engineer = RoleChecker(["admin", "quality_manager", "factory_supervisor", "quality_engineer"])
require_operator = RoleChecker(["admin", "quality_manager", "factory_supervisor", "quality_engineer", "operator"])
