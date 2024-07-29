from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('streamer/', include('streamer.urls')),
    path('manager/', include('manager.urls')),
]
