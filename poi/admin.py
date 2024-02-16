'''
File to add customization to admin site
'''
# Register your models here.
from django.contrib import admin

from .models import PointOfInterest

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    '''
    Custom admin to add customize search and filter options
    '''
    list_display = ('internal_id', 'name', 'external_id', 'category', 'ratings')
    search_fields = ('internal_id', 'external_id')
    list_filter = ('category',)
