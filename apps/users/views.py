from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from apps.core.constants import MARITAL_STATUSES
from apps.core.constants import UserRoles
from apps.properties.models import Property, PropertyUnit
from django.views.generic import ListView
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.http import HttpRequest

GENDERS = [
    "Male",
    "Female",
]

ROLES = [
    "Caretaker",
    "House Manager",
]


def login_user(request: HttpRequest):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        print("***********User Information***************")
        print(username, password)
        print("***********User Information***************")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "home")
            return redirect(next_url)  # Redirect to the next URL or home page.
        else:
            return redirect("login")
    next_url = request.GET.get("next", "")
    return render(request, "accounts/login.html", {"next": next_url})


@login_required
def logout_user(request: HttpRequest):
    logout(request)
    return redirect("login")  # Redirect to a login page.


class UserListView(ListView):
    model = User
    template_name = "users/users.html"
    context_object_name = "users"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | Q(first_name__icontains=search_query)
            )
        return queryset.exclude(role="Tenant").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["marital_statuses"] = MARITAL_STATUSES
        context["genders"] = ["Male", "Female"]
        context["roles"] = ["Caretaker", "House Manager"]
        return context


def new_user(request: HttpRequest):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        id_number = request.POST.get("id_number")
        gender = request.POST.get("gender")
        role = request.POST.get("role")
        marital_status = request.POST.get("marital_status")
        username = request.POST.get("username")

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            id_number=id_number,
            gender=gender,
            role=role,
            username=username,
            marital_status=marital_status,
        )
        user.set_password("1234")
        user.save()
        return redirect("users")
    return render(request, "users/new_user.html")


def edit_user(request: HttpRequest):
    user_object = User.objects.filter(id=request.GET.get("id")).first()
    print(f"User object: {user_object}")
    if request.method == "POST":
        user = User.objects.get(id=request.POST.get("user_id"))
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.id_number = request.POST.get("id_number")
        user.gender = request.POST.get("gender")
        user.role = request.POST.get("role")
        user.marital_status = request.POST.get("marital_status")
        user.username = request.POST.get("username")
        user.save()
        return redirect("users")
    return render(request, "users/edit_user.html", {"current_user": user_object, "marital_statuses": MARITAL_STATUSES, "genders": GENDERS, "roles": ROLES})


def delete_user(request: HttpRequest):
    if request.method == "POST":
        user = User.objects.get(id=request.POST.get("user_id"))
        user.delete()
        return redirect("users")
    return render(request, "users/delete_user.html")


def change_password(request: HttpRequest, id: int):
    user = User.objects.get(id=id)

    print(f"Changing password for user: {user.first_name} {user.last_name}")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        if password.casefold() == confirm_password.casefold():
            user.set_password(password)
            user.save()
            return redirect("users")
        else:
            messages.error("Passwords do not match!!")
        return redirect("change-password", id=id)
    return render(request, "users/change_password.html", {"current_user": user})


def landlord_onboarding(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        name = request.POST.get("name", "").strip()
        city = request.POST.get("city", "").strip()
        country = request.POST.get("country", "").strip()
        units_count = request.POST.get("units_count", "1").strip()

        if not all(
            [
                first_name,
                last_name,
                email,
                password,
                confirm_password,
                name,
                city,
                country,
                phone_number
            ]
        ):
            messages.error(request, "Please complete all required fields.")
            return render(request, "users/landlord_onboarding.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "users/landlord_onboarding.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with that email already exists.")
            return render(request, "users/landlord_onboarding.html")


        with transaction.atomic():
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone_number,
                username=email,
                role="Landlord",
            )
            user.set_password(password)
            user.save()

            Property.objects.create(
                owner=user,
                name=name,
                city=city,
                country=country,
                units=units_count,
            )

        login(request, user)
        messages.success(request, "Welcome to REMS! Your landlord account and starter property have been created.")
        return redirect("home")

    return render(request, "users/landlord_onboarding.html")
