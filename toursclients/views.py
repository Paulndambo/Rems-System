from datetime import datetime, timedelta
from django.conf import settings

from django.db.models import Q

from django.shortcuts import render, redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import TourClient, Message
from apps.core.constants import GENDER_CHOICES

from apps.core.models import UserAction
from apps.users.models import User, Attendance
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from apps.notifications.sms_sender import TiaraConnectSMSManager, birthday_message_template, holiday_message_template, rent_reminder_template
# Create your views here.
@login_required
def clients(request):
    clients_count = TourClient.objects.count()
    messages_count = Message.objects.count()
    
    context = {
        "clients_count": clients_count,
        "messages_count": messages_count

    }
    return render(request, 'clients/home.html', context)


class TourClientsListView(LoginRequiredMixin, ListView):
    model = TourClient
    template_name = "clients/clients.html"
    context_object_name = "clients"
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genders"] = GENDER_CHOICES
        return context
    
@login_required
def new_tour_client(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        id_number = request.POST.get('id_number')
        passport_number = request.POST.get('passport_number')
        email = request.POST.get('email')
        nationality = request.POST.get('nationality')
    
        tour_client = TourClient.objects.create(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            id_number=id_number,
            passport_number=passport_number,
            email=email,
            nationality=nationality
        )
        
        UserAction.objects.create(
            user=request.user,
            action_type="Added Tour Client",
            action_details=f"Added Tour Client: {tour_client.name}"
        )
        
        return redirect("tour-clients")
    return render(request, "clients/new_client.html")

@login_required
def edit_tour_client(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        id_number = request.POST.get('id_number')
        passport_number = request.POST.get('passport_number')
        email = request.POST.get('email')
        nationality = request.POST.get('nationality')
        
    
        TourClient.objects.filter(id=client_id).update(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            id_number=id_number,
            passport_number=passport_number,
            email=email,
            nationality=nationality
        )

        UserAction.objects.create(
            user=request.user,
            action_type="Edited Tour Client",
            action_details=f"Edited Tour Client: {first_name} {last_name}"
        )
        
        return redirect("tour-clients")
    return render(request, "clients/edit_client.html")

@login_required
def delete_tour_client(request):
    if request.method == "POST":
        tour_client_id = request.POST.get("client_id")
        tour_client = TourClient.objects.get(id=tour_client_id).delete()
        UserAction.objects.create(
            user=request.user,
            action_type="Deleted Tour Client",
            action_details=f"Deleted Tour Client: {tour_client.name}"
        )
        return redirect("tour-clients")
    return render(request, "clients/delete_client.html")


## Upcoming Birthdays
class UpcomingBirthdaysView(LoginRequiredMixin, ListView):
    model = TourClient
    template_name = 'clients/upcoming_birthdays.html'
    context_object_name = 'clients'
    paginate_by = 9

    def get_queryset(self):
        today = datetime.today().date()
        upcoming_dates = [(today + timedelta(days=i)) for i in range(0, 4)]

        birthday_filter = Q()
        for date in upcoming_dates:
            birthday_filter |= Q(dob__month=date.month, dob__day=date.day)

        return TourClient.objects.filter(birthday_filter)


## Messages
class BirthdayMessagesListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "clients/birthdays/messages.html"
    context_object_name = "messages"
    paginate_by = 9
    

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(receiver__name__icontains=search_query)
            )

        return queryset.filter(purpose="Birthday").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"] = TourClient.objects.all()
        return context


class HolidayMessagesListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "clients/messages/messages.html"
    context_object_name = "messages"
    paginate_by = 9
    

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(holiday_name__icontains=search_query)
            )

        return queryset.filter(purpose="Holiday").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

@login_required
def new_message(request):
    if request.method == 'POST':
        purpose = request.POST.get('purpose')
        receiver = request.POST.get('receiver')
        holiday_name = request.POST.get('holiday_name')
        holiday_date = request.POST.get('holiday_date')
        country = request.POST.get('country')
        
        if purpose.lower() == "birthday":
            message = Message.objects.create(
                purpose=purpose,
                receiver=TourClient.objects.get(id=receiver),
                country=country
            )
            UserAction.objects.create(
                user=request.user,
                action_type="Sent Birthday Message",
                action_details=f"Sent Birthday Message to: {message.receiver.name}"
            )
            
            try:
                TiaraConnectSMSManager(
                    phone_number=message.receiver.phone_number,
                    message=birthday_message_template(client=message.receiver)
                ).run()
                
            except Exception as e:
                print(e)
                
            
            return redirect("birthday-messages")
        
        elif purpose.lower() == "holiday":
            message = Message.objects.create(
                purpose=purpose,
                holiday_date=holiday_date,
                holiday_name=holiday_name,
                country=country
            )
            UserAction.objects.create(
                user=request.user,
                action_type="Sent Holiday Message",
                action_details=f"Sent Holiday Message to: {message.holiday_name}"
            )
            try:
                for client in TourClient.objects.all():
                    TiaraConnectSMSManager(
                        phone_number=client.phone_number,
                        message=holiday_message_template(
                            message=message, 
                            client=client
                        )
                    ).run()
                    
            except Exception as e:
                print(e)
            return redirect("holiday-messages")
        
    return render(request, "messages/new_message.html")

@login_required
def delete_message(request):
    if request.method == "POST":
        message_id = request.POST.get("message_id")
        purpose = request.POST.get("purpose").lower()
        message = Message.objects.get(id=message_id).delete()
        UserAction.objects.create(
            user=request.user,
            action_type="Deleted Message",
            action_details=f"Deleted Message: {message.purpose}"
        )
        return redirect(f"{purpose}-messages")
    return render(request, "clients/messages/delete_message.html")



class UserActionListView(LoginRequiredMixin, ListView):
    model = UserAction
    template_name = "clients/user_actions.html"
    context_object_name = "actions"
    paginate_by = 9
    

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = "clients/attendances.html"
    context_object_name = "attendances"
    paginate_by = 9
    

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
         

class LoggedInUsersView(ListView):
    template_name = 'clients/logged_in_users.html'
    context_object_name = 'users'

    def get_queryset(self):
        sessions = Session.objects.filter(expire_date__gte=now())
        users_data = []

        for session in sessions:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    login_time = session.expire_date - timedelta(seconds=settings.SESSION_COOKIE_AGE)
                    users_data.append({
                        'user': user,
                        'login_time': login_time
                    })
                except User.DoesNotExist:
                    continue

        return users_data

class EmployeeListView(ListView):
    model = User
    template_name = "clients/employees/employees.html"
    context_object_name = "employees"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | Q(first_name__icontains=search_query)
            )
        return queryset.filter(role="Employee").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["marital_statuses"] = ["Married", "Single", "Divorced"]
        context["genders"] = ["Male", "Female"]
        return context
    
    
def new_employee(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        id_number = request.POST.get("id_number")
        gender = request.POST.get("gender")
        marital_status = request.POST.get("marital_status")
        username = request.POST.get("username")

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            id_number=id_number,
            gender=gender,
            role="Employee",
            username=username,
            marital_status=marital_status,
        )
        user.set_password("1234")
        user.save()
        return redirect("employees")
    return render(request, "clients/employees/new_employee.html")


def edit_employee(request):
    if request.method == "POST":
        user = User.objects.get(id=request.POST.get("user_id"))
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.id_number = request.POST.get("id_number")
        user.gender = request.POST.get("gender")
        user.marital_status = request.POST.get("marital_status")
        user.username = request.POST.get("username")
        user.save()
        return redirect("employees")
    return render(request, "clients/employees/edit_employee.html")


def delete_employee(request):
    if request.method == "POST":
        user = User.objects.get(id=request.POST.get("user_id"))
        user.delete()
        return redirect("employees")
    return render(request, "clients/employees/delete_employee.html")