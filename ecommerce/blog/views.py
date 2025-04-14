from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Post, Category
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import PostForm
from django.contrib import messages
from .forms import CommentForm
from django.shortcuts import get_object_or_404, redirect
from .models import Comment
from django.contrib.auth.decorators import user_passes_test



def post_list(request):
    posts = Post.objects.filter(is_published=True, is_approved=True).exclude(slug__isnull=True).exclude(slug__exact='')
    categories = Category.objects.all()
    context = {
        'posts': posts,
        'categories': categories,
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comments = post.comments.all()
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            new_comment.save()
            messages.success(request, 'Votre commentaire a été soumis pour modération.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/post_detail.html', context)

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, is_published=True)
    categories = Category.objects.all()
    context = {
        'category': category,
        'posts': posts,
        'categories': categories,
    }
    return render(request, 'blog/category_posts.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_published = True  # L'article est soumis pour approbation
            post.is_approved = False  # Pas encore approuvé
            post.save()
            messages.success(request, "Votre article a été soumis pour approbation par l'administrateur.")
            return redirect('blog:post_list')
    else:
        form = PostForm()
    
    return render(request, 'blog/create_post.html', {'form': form})

@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "L'article a été mis à jour avec succès!")
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/edit_post.html', {'form': form, 'post': post})



@user_passes_test(lambda u: u.is_staff)  # Seul l'admin peut accéder
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', slug=comment.post.slug)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/edit_comment.html', {'form': form, 'comment': comment})

@user_passes_test(lambda u: u.is_staff)
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_slug = comment.post.slug
    comment.delete()
    return redirect('blog:post_detail', slug=post_slug)

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': comment.total_likes()
        })
    
    return redirect('blog:post_detail', slug=comment.post.slug)

@user_passes_test(lambda u: u.is_staff)
def post_moderation(request):
    pending_posts = Post.objects.filter(is_published=True, is_approved=False)
    return render(request, 'blog/post_moderation.html', {'pending_posts': pending_posts})

@user_passes_test(lambda u: u.is_staff)
def approve_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.is_approved = True
    post.save()
    messages.success(request, f"L'article '{post.title}' a été approuvé.")
    return redirect('blog:post_moderation')

@user_passes_test(lambda u: u.is_staff)
def reject_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.is_published = False
    post.save()
    messages.success(request, f"L'article '{post.title}' a été rejeté.")
    return redirect('blog:post_moderation')