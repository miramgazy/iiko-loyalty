from rest_framework import permissions
from apps.accounts.models import UserOrganization

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return UserOrganization.objects.filter(
            user=request.user,
            role__in=[UserOrganization.ROLE_SUPERUSER, UserOrganization.ROLE_SUPERADMIN]
        ).exists()

class IsOrgManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
            
        if UserOrganization.objects.filter(
            user=request.user,
            role__in=[UserOrganization.ROLE_SUPERUSER, UserOrganization.ROLE_SUPERADMIN]
        ).exists():
            return True

        org_id = view.kwargs.get('organization_id') or request.data.get('organization_id')
        if not org_id:
            org_id = request.query_params.get('organization_id')

        if not org_id:
            return False

        return UserOrganization.objects.filter(
            user=request.user,
            organization_id=org_id,
            role=UserOrganization.ROLE_ORG_MANAGER
        ).exists()

class IsOrgEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
            
        if UserOrganization.objects.filter(
            user=request.user,
            role__in=[UserOrganization.ROLE_SUPERUSER, UserOrganization.ROLE_SUPERADMIN]
        ).exists():
            return True

        org_id = view.kwargs.get('organization_id') or request.data.get('organization_id')
        if not org_id:
            org_id = request.query_params.get('organization_id')

        if not org_id:
            return False

        return UserOrganization.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=[UserOrganization.ROLE_ORG_MANAGER, UserOrganization.ROLE_ORG_ADMIN]
        ).exists()
