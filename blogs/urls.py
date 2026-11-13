from django.urls import path
from . import views

urlpatterns = [
    path('', views.blogs, name='blogs'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('blog/', views.blog, name='blog'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('blog/edit/<int:post_id>/', views.edit_blog, name='edit_blog'),
    path('blog/delete/<int:post_id>/', views.delete_blog, name='delete_blog'),
    path('my-blog/', views.my_blog, name='my_blog'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

]