from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def driver_required(view_func):
    """
    Decorator for views that checks if the user is logged in, has a driver profile,
    and has the DRIVER role.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login with next parameter
            path = request.get_full_path()
            return redirect(f'/accounts/login/?next={path}')
        
        # Check both role and driver_profile existence
        if hasattr(request.user, 'driver_profile') and getattr(request.user, 'profile', None) and request.user.profile.role == 'DRIVER':
            return view_func(request, *args, **kwargs)
        
        raise PermissionDenied("Access Denied: Only assigned drivers have access to this panel.")
    return _wrapped_view
