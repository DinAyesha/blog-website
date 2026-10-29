from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.
def blogs(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())
def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())
def signup(request):
 if request.method == "POST":
    fullname = request.POST.get("fullname")
    email = request.POST.get("email")
    password = request.POST.get("password")
    confirm_password = request.POST.get("confirm-password")
    terms = request.POST.get("terms")

    print(fullname)
    print(email)
    print("Password received:", bool(password))
    print("Confirm_password received:", bool(confirm_password))
    print("Terms accepted:", terms == "yes")

 return render (request, 'signup.html')



def blog(request):
    template = loader.get_template('blog.html')
    return HttpResponse(template.render())