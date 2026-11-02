from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login

# Create your views here.
def blogs(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())
def login(request):
    if request.method == "POST":
       email = request.POST.get("email", "").strip().lower()
       password = request.POST.get("password", "")

       user = authenticate(
          request,
          username=email,
          password=password
       )

       if not user:
          messages.error(request, "Invalid email or password")
          return render(request,"login.html")
       
       auth_login(request,user)
       return redirect("blogs")
    
    return render(request,"login.html")

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
    template = loader.get_template('blog.html')
    return HttpResponse(template.render())