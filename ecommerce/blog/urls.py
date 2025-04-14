from django.urls import path
from . import views

app_name = 'blog'



urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('nouveau/', views.create_post, name='create_post'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('editer/<slug:slug>/', views.edit_post, name='edit_post'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('moderation/', views.post_moderation, name='post_moderation'),
    path('approve/<slug:slug>/', views.approve_post, name='approve_post'),
    path('reject/<slug:slug>/', views.reject_post, name='reject_post'),
    ]