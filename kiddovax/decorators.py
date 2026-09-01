from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    """
    Decorator for views to enforce role-based session authentication.
    allowed_roles: string (e.g., 'admin') or list/tuple of strings (e.g., ['admin', 'hospital'])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            session_role = request.session.get('user_role')
            session_cname = request.session.get('CName')

            # Check both session CName presence and user_role matching
            if not session_cname or not session_role or session_role not in allowed_roles:
                messages.error(request, "Access denied. Please log in with the appropriate account credentials.")
                
                # Redirect to the corresponding login page based on target role
                role_redirects = {
                    'admin': 'adminapp:adminlogin',
                    'hospital': 'hospitalapp:hospitallogin',
                    'receptionist': 'receptionist:receptionistlogin',
                    'patient': 'patient:loginpage',
                }
                for role in allowed_roles:
                    if role in role_redirects:
                        return redirect(role_redirects[role])
                return redirect('patient:loginpage')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
