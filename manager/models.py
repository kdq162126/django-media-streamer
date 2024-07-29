from django.db import models

class Preference(models.Model):
    id = models.BigAutoField(primary_key=True)  # Explicitly set BigAutoField
    media_src_dir = models.CharField(max_length=255)
    media_cache_dir = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Preference'
        verbose_name_plural = 'Preferences'

class Library(models.Model):
    MEDIA_TYPE_VIDEO = 'VID'
    MEDIA_TYPE_AUDIO = 'AUD'
    MEDIA_TYPES = (
        (MEDIA_TYPE_VIDEO, 'Video'),
        (MEDIA_TYPE_AUDIO, 'Audio')
    )

    id = models.BigAutoField(primary_key=True)  # Explicitly set BigAutoField
    cache_hash_name = models.CharField(max_length=255)
    media_title = models.CharField(max_length=255)
    media_type = models.CharField(max_length=4, choices=MEDIA_TYPES)

    class Meta:
        verbose_name = 'Library'
        verbose_name_plural = 'Libraries'
