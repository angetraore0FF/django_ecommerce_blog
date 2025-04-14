from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    slug = models.SlugField(unique=True, blank=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True)
    published_date = models.DateTimeField(default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)  # Changé à False par défaut
    is_approved = models.BooleanField(default=False)  # Nouveau champ pour l'approbation admin

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']
        permissions = [
            ("can_publish_post", "Peut publier des articles"),
            ("can_approve_post", "Peut approuver des articles"),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

User = get_user_model()

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    def total_likes(self):
        return self.likes.count()