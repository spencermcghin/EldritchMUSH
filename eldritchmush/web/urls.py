"""
Url definition file to redistribute incoming URL requests to django
views. Search the Django documentation for "URL dispatcher" for more
help.

"""
from django.urls import re_path as url, include, path

# default evennia patterns
from evennia.web.urls import urlpatterns

from web.api_views import webclient_session, account_characters

# eventual custom patterns
custom_patterns = [
    # JSON endpoints used by the React frontend
    path("api/webclient_session/", webclient_session, name="webclient_session"),
    path("api/account/characters/", account_characters, name="account_characters"),
]

# Mount allauth URLs only if django-allauth is installed. Defensive so
# the server boots even on environments without the optional dep.
try:
    import allauth  # noqa: F401
    custom_patterns.append(path("accounts/", include("allauth.urls")))
except ImportError:
    pass

# this is required by Django.
urlpatterns = custom_patterns + urlpatterns
