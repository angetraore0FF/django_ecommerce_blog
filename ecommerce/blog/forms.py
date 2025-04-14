from django import forms
from .models import Post
from django.utils.text import slugify
from .models import Comment



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'category', 'content', 'image', 'is_published']
    
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        if title:
            cleaned_data['slug'] = slugify(title)
        return cleaned_data
    

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ajoutez votre commentaire...'
            }),
        }