from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.blogs, name='blogs'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('password-reset/',auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.txt',
        html_email_template_name='base_email.html',
        subject_template_name='password_reset_subject.txt',
        extra_email_context={
            'email_type': 'password_reset',
            'email_title': 'Reset Your Password',
            'message': 'We received a request to reset your MyBlog account password.'
        },
        success_url=reverse_lazy('password_reset_done')
    ),
    name='password_reset'
),


    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path('password-reset-complete/',auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('blog/', views.blog, name='blog'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('blog/edit/<int:post_id>/', views.edit_blog, name='edit_blog'),
    path('blog/delete/<int:post_id>/', views.delete_blog, name='delete_blog'),
    path('my-blog/', views.my_blog, name='my_blog'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-manage-users/',views.admin_manage_users,name='admin_manage_users'),
    path('admin-dashboard/blogs/',views.admin_manage_blogs,name='admin_manage_blogs'),
    path('admin-manage-categories/',views.admin_manage_categories,name='admin_manage_categories'),
    
]