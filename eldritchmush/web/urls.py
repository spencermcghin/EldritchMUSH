"""
Url definition file to redistribute incoming URL requests to django
views. Search the Django documentation for "URL dispatcher" for more
help.

"""
from django.urls import re_path as url, include, path

# default evennia patterns
from evennia.web.urls import urlpatterns

from web.api_views import webclient_session

# eventual custom patterns
custom_patterns = [
    # OAuth (Google sign-in via django-allauth)
    path("accounts/", include("allauth.urls")),
    # JSON endpoint the React frontend hits to discover its csessid
    path("api/webclient_session/", webclient_session, name="webclient_session"),
]

# this is required by Django.
urlpatterns = custom_patterns + urlpatterns
