from django.contrib import admin
from .models import Category, Post, Comment
from django import forms

# Formulaire personnalisé pour les commentaires
class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published_date', 'is_published')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    form = CommentAdminForm
    list_display = ('author', 'post', 'truncated_content', 'created_date')
    list_filter = ('created_date','author')
    search_fields = ('author__username', 'content')
    actions = ['approve_comments', 'disapprove_comments']
    
    def truncated_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Contenu'
    
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approuver les commentaires sélectionnés"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(approved=False)
    disapprove_comments.short_description = "Désapprouver les commentaires sélectionnés"