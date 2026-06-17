from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def admin_required(view_func):
    """
    Decorator for views that checks if the user is logged in, and is an admin
    (either is_superuser, is_staff, or has ADMIN role in profile).
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            path = request.get_full_path()
            return redirect(f'/accounts/login/?next={path}')
        
        is_admin = False
        if request.user.is_superuser or request.user.is_staff:
            is_admin = True
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN':
            is_admin = True
            
        if is_admin:
            return view_func(request, *args, **kwargs)
            
        raise PermissionDenied("Access Denied: You do not have permissions to access the Admin Panel.")
    return _wrapped_view
