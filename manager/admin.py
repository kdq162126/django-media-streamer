from django.contrib import admin

from .models import *


class PreferenceAdmin(admin.ModelAdmin):
    pass


class LibraryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Preference, PreferenceAdmin)
admin.site.register(Library, LibraryAdmin)