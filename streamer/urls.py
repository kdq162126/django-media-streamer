from django.urls import re_path
from . import views  # Import views properly

urlpatterns = [
    re_path(r'(?P<stream_path>.*)/$', views.get_stream, name='get_stream'),
]
