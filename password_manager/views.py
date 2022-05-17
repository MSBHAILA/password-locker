from multiprocessing import context
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
import random
from django.core .mail import send_mail
from cryptography.fernet import Fernet
import favicon
from mechanize import Browser
from .models import Password


br = Browser()
br.set_handle_robots(False)
fernet = Fernet(settings.KEY)

# Create your views here.

def index(request):

    if request.method == "POST":
        if "signup-form" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            
            #if passwords do not match
            if password != password2:
                msg = "Passwords are not matching"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            #if username exists
            elif User.objects.filter(username=username).exists():
                msg = f"{username} already exists!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            elif User.objects.filter(email=email).exists():
                msg = f"{email} already exists!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                User.objects.create_user(username, email, password)
                new_user = authenticate(request, username=username, password=password2)
                if new_user is not None:
                    login(request, new_user)
                    msg = f"{username} Registered Successfully!"
                    messages.success(request, msg)
                    return HttpResponseRedirect(request.path)
        elif "logout" in request.POST:
            msg = f"{request.user}. You logged out."
            logout(request)
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif "login-form" in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            new_login = authenticate(request, username=username, password=password)
            if new_login is None:
                msg = f"Login Failed"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                code = str(random.randint(100000, 999999))
                global global_code
                global_code = code
                send_mail(
                    "Django Password Manager: confirm email",
                    f"Your verification code is {code}.",
                    settings.EMAIL_HOST_USER,
                    [new_login.email],
                    fail_silently=False,
                )
                return render(request, "index.html", {"code":code,
                    "user":new_login,
                })

        elif "confirm" in request.POST:
            input_code = request.POST.get("code")
            user = request.POST.get("user")
            if global_code != input_code:
                msg = f"{input_code} is wrong!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                login(request, User.objects.get(username=user))
                msg = f"Welcome Again {request.user}"
                messages.success(request, msg)
                return HttpResponseRedirect(request.path)
        
        elif "add-password" in request.POST:
            url = request.POST.get("url")
            email = request.POST.get("email")
            password = request.POST.get("password")
            #encrypt password and email
            encrypted_email = fernet.encrypt(email.encode())
            encrypted_password = fernet.encrypt(password.encode())
            #title of the website
            br.open(url)
            title = br.title()
            #logo of the website
            icon = favicon.get(url)[0].url
            #Saving data in database
            new_password = Password.objects.create(
                user = request.user,
                name = title,
                logo = icon,
                email = encrypted_email.decode(),
                password = encrypted_password.decode(),
            )
            msg = f"{title} Added Successfully!"
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif "delete" in request.POST:
            to_delete = request.POST.get("password-id")
            msg = f"{Password.objects.get(id=to_delete).name} Deleted!"
            messages.success(request, msg)
            Password.objects.get(id=to_delete).delete()
            return HttpResponseRedirect(request.path)

    context = {}
    countid = []
    if request.user.is_authenticated:
        passwords = Password.objects.all().filter(user=request.user)
        if passwords.exists():
            exists = True
        for password in passwords:
            password.email = fernet.decrypt(password.email.encode()).decode()
            password.password = fernet.decrypt(password.password.encode()).decode()
            context = {
            "passwords":passwords,
            "exists": exists,
        }

    return render(request, "index.html", context)

# def log_out(request):
#     # msg = f"Logged Out Successfully!"
#     # messages.success(request, msg)
#     logout(request)
#     return render(request, "index.html", {})  