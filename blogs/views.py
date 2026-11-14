from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.template import loader
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
from .models import BlogPost, Category
from .models import Category, BlogPost, UserProfile
from .forms import UserUpdateForm, UserProfileForm
from .models import UserProfile
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.utils.http import url_has_allowed_host_and_scheme
from PIL import Image
from PIL import UnidentifiedImageError
from django.core.mail import send_mail
from django.contrib import messages

# Create your views here.
def blogs(request):
    latest_posts = BlogPost.objects.filter(
        status='published'
    ).select_related(
        'author', 'category'
    ).order_by('-created_at')[:3]

    categories = Category.objects.all()

    context = {
        'latest_posts': latest_posts,
        'categories': categories,
    }

    return render(request, 'home.html', context)


def login(request):
    email_error = None
    password_error = None
    email_value = ""

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        email_value = email

        if not email:
            email_error = "Please enter your email."
        else:
            try:
                validate_email(email)
            except ValidationError:
                email_error = "Please enter a valid email address."

        if not password:
            password_error = "Please enter your password."

        if email_error or password_error:
            context = {
                'email_error': email_error,
                'password_error': password_error,
                'email_value': email_value,
                'next_url': next_url,
            }
            return render(request, "login.html", context)

        user_obj = User.objects.filter(email__iexact=email).first()

        if user_obj:
            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )
        else:
            user = None

        if not user:
            password_error = "Invalid email or password."

            context = {
                'email_error': email_error,
                'password_error': password_error,
                'email_value': email_value,
                'next_url': next_url,
            }
            return render(request, "login.html", context)

        auth_login(request, user)

        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

        return redirect('blogs')

    context = {
        'email_error': email_error,
        'password_error': password_error,
        'email_value': email_value,
        'next_url': next_url,
    }

    return render(request, "login.html", context)


def logout_view(request):
   logout(request)

   return redirect("blogs")


def signup(request):

    fullname_error = None
    email_error = None
    password_error = None
    confirm_password_error = None
    terms_error = None

    fullname_value = ""
    email_value = ""
    terms_accepted = False

    if request.method == "POST":

        fullname = request.POST.get("fullname", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm-password", "")
        terms = request.POST.get("terms")

        fullname_value = fullname
        email_value = email
        terms_accepted = terms == "yes"

        if not fullname:
            fullname_error = "Please enter your full name."

        if not email:
            email_error = "Please enter your email."
        else:
            try:
                validate_email(email)
            except ValidationError:
                email_error = "Please enter a valid email address."
            else:
                if User.objects.filter(email__iexact=email).exists():
                    email_error = "This email is already registered."

                elif len(email) > 150 or User.objects.filter(username=email).exists():
                    email_error = "This email cannot be used as a username."

        if not password:
            password_error = "Please enter your password."

        elif len(password) < 8:
            password_error = "Password must contain at least 8 characters."

        else:
            try:
                validate_password(password)
            except ValidationError as error:
                password_error = " ".join(error.messages)

        if not confirm_password:
            confirm_password_error = "Please confirm your password."

        elif password != confirm_password:
            confirm_password_error = "Passwords do not match."

        if not terms_accepted:
            terms_error = "Please accept Terms and Conditions."

        if any([
            fullname_error,
            email_error,
            password_error,
            confirm_password_error,
            terms_error
        ]):
            context = {
                'fullname_error': fullname_error,
                'email_error': email_error,
                'password_error': password_error,
                'confirm_password_error': confirm_password_error,
                'terms_error': terms_error,
                'fullname_value': fullname_value,
                'email_value': email_value,
                'terms_accepted': terms_accepted,
            }

            return render(request, "signup.html", context)

        name_parts = fullname.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])

        username = email

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(user=user)

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    context = {
        'fullname_error': fullname_error,
        'email_error': email_error,
        'password_error': password_error,
        'confirm_password_error': confirm_password_error,
        'terms_error': terms_error,
        'fullname_value': fullname_value,
        'email_value': email_value,
        'terms_accepted': terms_accepted,
    }

    return render(request, "signup.html", context)


@login_required
def edit_profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    password_error = None
    confirm_password_error = None

    if request.method == 'POST':

        user_form = UserUpdateForm(
            request.POST,
            instance=request.user
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password:

            try:
                validate_password(new_password, request.user)

            except ValidationError as error:
                password_error = " ".join(error.messages)

            if not confirm_password:
                confirm_password_error = "Please confirm your new password."

            elif new_password != confirm_password:
                confirm_password_error = "Passwords do not match."

        elif confirm_password:
            password_error = "Please enter a new password first."

        user_valid = user_form.is_valid()
        profile_valid = profile_form.is_valid()
        

        if (
            user_valid
            and profile_valid
            and not password_error
            and not confirm_password_error
        ):

            user_form.save()
            profile_form.save()

            if new_password:
                request.user.set_password(new_password)
                request.user.save()

                update_session_auth_hash(request, request.user)

            messages.success(
                request,
                "Your profile has been updated successfully!"
            )

            return redirect('edit_profile')

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_error': password_error,
        'confirm_password_error': confirm_password_error,
    }

    return render(request, 'edit_profile.html', context)
@login_required
def change_password(request):

    if request.method != 'POST':
        return redirect('edit_profile')

    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    password_error = None
    confirm_password_error = None

    if not new_password:
        password_error = "Please enter a new password."

    else:
        try:
            validate_password(new_password, user=request.user)

        except ValidationError as errors:
            password_error = " ".join(errors.messages)

    if not confirm_password:
        confirm_password_error = "Please confirm your new password."

    elif new_password != confirm_password:
        confirm_password_error = "Passwords do not match."

    if password_error or confirm_password_error:

        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'password_error': password_error,
            'confirm_password_error': confirm_password_error,
        }

        return render(request, 'edit_profile.html', context)

    request.user.set_password(new_password)
    request.user.save()

    update_session_auth_hash(request, request.user)

    messages.success(
        request,
        "Your password has been updated successfully!"
    )

    return redirect('edit_profile')



def blog(request):
    posts = BlogPost.objects.filter(
       status = 'published'
    ).select_related('author', 'category').order_by('-created_at')

    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()

    selected_category = None

    if category_id and category_id.isdigit():
       selected_category = Category.objects.filter(
          id=category_id
       ).first()

       posts = posts.filter(category_id=category_id)

    if search_query:
       posts = posts.filter(
          Q(title__icontains=search_query) |
          Q(content__icontains=search_query) |
          Q(category__name__icontains=search_query) |
          Q(author__username__icontains=search_query) |
          Q(author__first_name__icontains=search_query) |
          Q(author__last_name__icontains=search_query)
    )

    categories = Category.objects.all()
    context = {
       'posts': posts,
       'categories': categories,
       'selected_category': selected_category,
       'search_query': search_query,
    }
    

    return render(request, "blog.html", context)

def blog_detail(request, post_id):
    post = BlogPost.objects.select_related(
        'author', 'category'
    ).get(
        id=post_id,
        status='published'
    )

    context = {
        'post': post,
        'next_page': request.GET.get('next', '/'),
    }

    return render(request, 'blog_detail.html', context)

@login_required
def create_blog(request):

    if request.user.is_staff:
        messages.error(request, "Admins are not allowed to create blog posts.")
        return redirect('blog')

    categories = Category.objects.all()

    title_error = None
    image_error = None
    category_error = None
    content_error = None

    title_value = ""
    content_value = ""
    category_value = ""
    status_published = True

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        status_published = request.POST.get('status') == 'published'
        status = 'published' if status_published else 'draft'

        title_value = title
        content_value = content
        category_value = category_id or ""

        if not title:
            title_error = "Please enter a blog title."

        if not content:
            content_error = "Please enter your blog content."

        category = None

        if category_id:
            category = Category.objects.filter(
                id=category_id
            ).first()

            if category is None:
                category_error = "Please select a valid category."

        if image:
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)

            except (UnidentifiedImageError, OSError, ValueError):
                image_error = "Please upload a valid image file."

        if not any([
            title_error,
            content_error,
            category_error,
            image_error
        ]):

            BlogPost.objects.create(
                title=title,
                image=image,
                category=category,
                content=content,
                author=request.user,
                status=status
            )

            messages.success(request, "Blog created successfully!")
            return redirect('blog')

    context = {
        'categories': categories,
        'title_error': title_error,
        'image_error': image_error,
        'category_error': category_error,
        'content_error': content_error,
        'title_value': title_value,
        'content_value': content_value,
        'category_value': category_value,
        'status_published': status_published,
    }

    return render(request, 'create_blog.html', context)

@login_required
def edit_blog(request,post_id):

    if request.user.is_staff:
        return HttpResponseForbidden("Admin cannot edit blogs.")

    post = get_object_or_404(
        BlogPost,
        id=post_id,
        author=request.user
    )

    categories = Category.objects.all()

    title_error = None
    category_error = None
    content_error = None
    image_error = None
    status_error = None

    title_value = post.title
    content_value = post.content
    category_value = str(post.category_id or '')
    status_value = post.status

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category', '')
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        status = request.POST.get('status', 'draft')

        title_value = title
        content_value = content
        category_value = category_id
        status_value = status

        if not title:
            title_error = "Please enter a blog title."

        if not content:
            content_error = "Please enter your blog content."

        category = None

        if category_id:
            category = Category.objects.filter(
                id=category_id
            ).first()

            if category is None:
                category_error = "Please select a valid category."

        if status not in ['draft', 'published']:
            status_error = "Invalid blog status."

        if image:
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)

            except (UnidentifiedImageError, OSError, ValueError):
                image_error = "Please upload a valid image file."

        if not any([
            title_error,
            category_error,
            content_error,
            image_error,
            status_error
        ]):

            post.title = title
            post.category = category
            post.content = content
            post.status = status

            if image:
                post.image = image

            post.save()

            messages.success(
                request,
                "Blog updated successfully!"
            )

            return redirect('blog')

    context = {
        'post': post,
        'categories': categories,
        'title_error': title_error,
        'category_error': category_error,
        'content_error': content_error,
        'image_error': image_error,
        'status_error': status_error,
        'title_value': title_value,
        'content_value': content_value,
        'category_value': category_value,
        'status_published': status_value == 'published',
    }

    return render(request, 'edit_blog.html', context)

@login_required
def delete_blog(request, post_id):

    if request.method != 'POST':
        return redirect('blog')

    if request.user.is_staff:
        post = get_object_or_404(
            BlogPost,
            id=post_id
        )

    else:
        post = get_object_or_404(
            BlogPost,
            id=post_id,
            author=request.user
        )

    post.delete()

    messages.success(request, "Blog deleted successfully!")

    return redirect('blog')

@login_required
def my_blog(request):

    posts = BlogPost.objects.filter(
        author=request.user
    ).select_related(
        'author', 'category'
    ).order_by('-created_at')

    search_query = request.GET.get('search', '').strip()

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    context = {
        'posts': posts,
        'search_query': search_query
    }

    return render(request, 'my_blog.html', context)


def about(request):
    return render(request, 'about.html')



def contact(request):

    email_error = None
    contact_message = None
    contact_message_type = None

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not subject or not message:
            contact_message = "All fields are required."
            contact_message_type = "error"

        else:
            try:
                validate_email(email)

            except ValidationError:
                email_error = "Please enter a valid email address."

            else:

                email_message = f"""
New Contact Message from MyBlog

Name: {name}
Email: {email}

Message:
{message}
"""

                try:
                    send_mail(
                        subject=subject,
                        message=email_message,
                        from_email=None,
                        recipient_list=['test@example.com'],
                        fail_silently=False,
                    )

                    contact_message = "Your message has been sent successfully!"
                    contact_message_type = "success"

                except Exception as e:
                    print("EMAIL SENDING ERROR:", e)

                    contact_message = "Sorry, your message could not be sent. Please try again."
                    contact_message_type = "error"

    context = {
        'email_error': email_error,
        'contact_message': contact_message,
        'contact_message_type': contact_message_type,
    }

    return render(request, 'contact.html', context)

@user_passes_test(lambda user: user.is_superuser, login_url='login')
def admin_dashboard(request):

    total_users = User.objects.count()

    total_blogs = BlogPost.objects.count()

    total_categories = Category.objects.count()

    published_blogs = BlogPost.objects.filter(
        status='published'
    ).count()

    recent_posts = BlogPost.objects.select_related(
        'author', 'category'
    ).order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_blogs': total_blogs,
        'total_categories': total_categories,
        'published_blogs': published_blogs,
        'recent_posts': recent_posts,
    }

    return render(request, 'admin_dashboard.html', context)


@user_passes_test(
    lambda user: user.is_superuser,
    login_url='login'
)
def admin_manage_users(request):

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if not user_id:
            messages.error(request, "User ID is missing.")
            return redirect('admin_manage_users')

        target_user = get_object_or_404(User, pk=user_id)

        # Admin cannot manage their own account from this page.
        if target_user.pk == request.user.pk:
            messages.error(request, "You cannot manage your own account here.")
            return redirect('admin_manage_users')

        # Protect superuser accounts.
        if target_user.is_superuser:
            messages.error(request, "Superuser accounts cannot be changed here.")
            return redirect('admin_manage_users')

        if action == 'activate':
            target_user.is_active = True
            target_user.save()
            messages.success(request, "User activated successfully.")

        elif action == 'deactivate':
            target_user.is_active = False
            target_user.save()
            messages.success(request, "User deactivated successfully.")

        elif action == 'delete':

            # Do not delete users who still have blog posts.
            if BlogPost.objects.filter(author=target_user).exists():
                messages.error(
                    request,
                    "This user has blog posts. Delete or reassign those posts first."
                )
            else:
                target_user.delete()
                messages.success(request, "User deleted successfully.")

        else:
            messages.error(request, "Invalid action.")

        return redirect('admin_manage_users')

    users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users,
    }

    return render(request, 'admin_manage_users.html', context)

@user_passes_test(
    lambda user: user.is_superuser,
    login_url='login'
)
def admin_manage_blogs(request):

    if request.method == 'POST':
        action = request.POST.get('action')
        post_id = request.POST.get('post_id')

        if action == 'delete' and post_id:
            post = get_object_or_404(BlogPost, pk=post_id)
            post.delete()
            messages.success(request, "Blog post deleted successfully.")

        else:
            messages.error(request, "Invalid request.")

        return redirect('admin_manage_blogs')

    posts = BlogPost.objects.select_related(
        'author', 'category'
    ).order_by('-created_at')

    context = {
        'posts': posts,
    }

    return render(request, 'admin_manage_blogs.html', context)


@user_passes_test(
    lambda user: user.is_superuser,
    login_url='login'
)
def admin_manage_categories(request):

    if request.method == 'POST':
        action = request.POST.get('action')
        category_id = request.POST.get('category_id')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()

            if not name:
                messages.error(request, "Category name is required.")

            elif Category.objects.filter(name__iexact=name).exists():
                messages.error(request, "This category already exists.")

            else:
                Category.objects.create(
                    name=name,
                    description=description
                )
                messages.success(request, "Category added successfully.")

        elif action == 'edit':
            if not category_id:
                messages.error(request, "Category ID is missing.")
                return redirect('admin_manage_categories')

            category = get_object_or_404(Category, pk=category_id)

            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()

            if not name:
                messages.error(request, "Category name is required.")

            elif Category.objects.filter(
                name__iexact=name
            ).exclude(pk=category.pk).exists():
                messages.error(request, "This category already exists.")

            else:
                category.name = name
                category.description = description
                category.save()
                messages.success(request, "Category updated successfully.")

        elif action == 'delete':
            if not category_id:
                messages.error(request, "Category ID is missing.")
                return redirect('admin_manage_categories')

            category = get_object_or_404(Category, pk=category_id)

            # Category uses PROTECT, so prevent deletion if blogs use it.
            if BlogPost.objects.filter(category=category).exists():
                messages.error(
                    request,
                    "This category is being used by blog posts and cannot be deleted."
                )
            else:
                category.delete()
                messages.success(request, "Category deleted successfully.")

        else:
            messages.error(request, "Invalid action.")

        return redirect('admin_manage_categories')

    categories = Category.objects.all().order_by('name')

    context = {
        'categories': categories,
    }

    return render(request, 'admin_manage_categories.html', context)