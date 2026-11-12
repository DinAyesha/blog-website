from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.template import loader
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from .models import BlogPost, Category
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from PIL import Image
from PIL import UnidentifiedImageError

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
    if request.method == "POST":
       email = request.POST.get("email", "").strip().lower()
       password = request.POST.get("password", "")

       if not email:
          messages.error(request,"Please enter your email.")
          return render(request,"login.html")
       if not password:
          messages.error(request,"Please enter your password.")
          return render(request,"login.html")
       try:
          validate_email(email)
       except ValidationError as error:
          messages.error(request,"Please enter a valid email address.")
          return render(request,"login.html")
       
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
          messages.error(request, "Invalid email or password")
          return render(request,"login.html")
       
       auth_login(request,user)
       messages.success(request,"Login successful!")
       return redirect("blogs")
    
    return render(request,"login.html")

def logout_view(request):
   logout(request)

   return redirect("blogs")

def signup(request):

    if request.method == "POST":
       fullname = request.POST.get("fullname", "").strip()
       email = request.POST.get("email", "").strip().lower()
       password = request.POST.get("password", "")
       confirm_password = request.POST.get("confirm-password", "")
       terms = request.POST.get("terms")

       name_parts = fullname.split()
       first_name = name_parts[0] if name_parts else ""
       last_name = " ".join(name_parts[1:])

       if not fullname:
          messages.error(request, "Please enter your full name.")
          return render(request, "signup.html")

       if not email:
          messages.error(request, "Please enter your email.")
          return render(request, "signup.html")
       try:
          validate_email(email)
       except ValidationError:
          messages.error(request, "Please enter a valid email address.")
          return render(request, "signup.html")

       if User.objects.filter(email__iexact=email).exists():
          messages.error(request,"This email is already registered.")
          return render(request, "signup.html")   

       username=email
       if len(username) >150 or User.objects.filter(username=username).exists():
          messages.error(request, "This email cannot be used as a username.")
          return render(request, "signup.html")
       
       if len (password) < 8:
          messages.error(request,"Password must contain at least 8 characters.")
          return render(request, "signup.html")
       try:
          validate_password(password)
       except ValidationError as error:
          for message in error.messages:
             messages.error(request,message)
             return render(request,"signup.html")

       
       if password != confirm_password:
          messages.error(request, "Passwords do not match.")
          return render(request, "signup.html")
       
       if terms != "yes":
          messages.error(request, "Please accept Terms and conditions.")
          return render(request, "signup.html")
       
       User.objects.create_user(
          username=username,
          email=email,
          password=password,
          first_name=first_name,
          last_name=last_name
        )
    
       messages.success(request, "Account created successfully! Please log in.")
       return redirect("login")

    return render(request, "signup.html")

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
          Q(content__icontains=search_query)
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

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        status = request.POST.get('status', 'draft')

        if not title or not content:
            messages.error(request, "Title and Content are required.")

        elif status not in ['draft', 'published']:
            messages.error(request, "Invalid blog status.")

        else:
            category = None

            if category_id:
                category = Category.objects.filter(
                    id=category_id
                ).first()

                if category is None:
                    messages.error(request, "Invalid category.")
                    return render(
                        request,
                        'create_blog.html',
                        {'categories': categories}
                    )

            if image:
                try:
                    img = Image.open(image)
                    img.verify()
                    image.seek(0)

                except (UnidentifiedImageError, OSError, ValueError):
                    messages.error(
                        request,
                        "Please upload a valid image file."
                    )
                    return render(
                        request,
                        'create_blog.html',
                        {'categories': categories}
                    )

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
    }

    return render(request, 'create_blog.html', context)

@login_required
def edit_blog(request, post_id):

    if request.user.is_staff:
        return HttpResponseForbidden("Admin cannot edit blogs.")

    post = get_object_or_404(
        BlogPost,
        id=post_id,
        author=request.user
    )

    categories = Category.objects.all()

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        status = request.POST.get('status', 'draft')

        if not title or not content:
            messages.error(request, "Title and Content are required.")

        elif status not in ['draft', 'published']:
            messages.error(request, "Invalid blog status.")

        else:
            category = None

            if category_id:
                category = Category.objects.filter(
                    id=category_id
                ).first()

                if category is None:
                    messages.error(request, "Invalid category.")
                    return render(
                        request,
                        'edit_blog.html',
                        {
                            'post': post,
                            'categories': categories
                        }
                    )

            post.title = title
            post.category = category
            post.content = content
            post.status = status

        if image:
            try:
               img = Image.open(image)
               img.verify()
               image.seek(0)
            except (UnidentifiedImageError, OSError, ValueError):
               messages.error(request, "Please upload a valid image file.")
               return render(request, 'edit_blog.html',
                   {
                      'post': post,
                      'categories': categories,
                   }                       
                )

            post.image = image
            post.save()

            messages.success(request, "Blog updated successfully!")

            return redirect('blog')

    context = {
        'post': post,
        'categories': categories,
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

    context = {
        'posts': posts,
    }

    return render(request, 'my_blog.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')