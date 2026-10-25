from django.urls import path
from . import views

urlpatterns = [
    path('blogs/', views.blogs, name='blogs'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('blog/', views.blog, name='blog'),


]