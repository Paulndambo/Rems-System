from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)  # Redirect to the next URL or home page.
        else:
            return HttpResponse('Invalid login credentials')
    next_url = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {'next': next_url})

@login_required
def logout_user(request):
    logout(request)
    return redirect('login')  # Redirect to a login page.