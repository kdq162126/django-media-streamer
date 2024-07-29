from django.urls import re_path
from manager.views import tests

urlpatterns = [
    re_path(r'^test_simple/$', tests.simple_stream, name='test_simple'),
    re_path(r'^test_dash/$', tests.dash_stream, name='test_dash'),
    re_path(r'^test_hls/$', tests.hls_stream, name='test_hls'),
]
