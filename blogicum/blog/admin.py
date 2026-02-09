from django.contrib import admin
from .models import Category, Location, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'author',
                    'pub_date',
                    'is_published',
                    'category',
                    'location'
                    )
    list_filter = ('is_published', 'pub_date', 'category', 'author')
    search_fields = ('title', 'text')
    list_editable = ('is_published', 'category', 'location')
    date_hierarchy = 'pub_date'
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title',
                'text',
                'image',
                'author',
                'category',
                'location'
            )
        }),
        ('Дата и время', {
            'fields': ('pub_date', 'created_at')
        }),
        ('Публикация', {
            'fields': ('is_published',),
            'description': 'Настройки видимости публикации'
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('text',)
