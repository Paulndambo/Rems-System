from datetime import datetime, timedelta

from django.db.models import Q

from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import TourClient, Message
from apps.core.constants import GENDER_CHOICES

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
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        id_number = request.POST.get('id_number')
        passport_number = request.POST.get('passport_number')
        email = request.POST.get('email')
        nationality = request.POST.get('nationality')
    
        tour_client = TourClient.objects.create(
            name=name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            id_number=id_number,
            passport_number=passport_number,
            email=email,
            nationality=nationality
        )
        
        return redirect("tour-clients")
    return render(request, "clients/new_client.html")

@login_required
def edit_tour_client(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        id_number = request.POST.get('id_number')
        passport_number = request.POST.get('passport_number')
        email = request.POST.get('email')
        nationality = request.POST.get('nationality')
        
    
        client = TourClient.objects.filter(id=client_id).update(
            name=name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            id_number=id_number,
            passport_number=passport_number,
            email=email,
            nationality=nationality
        )
        
        return redirect("tour-clients")
    return render(request, "clients/edit_client.html")

@login_required
def delete_tour_client(request):
    if request.method == "POST":
        tour_client_id = request.POST.get("client_id")
        TourClient.objects.get(id=tour_client_id).delete()
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
        Message.objects.get(id=message_id).delete()
        return redirect(f"{purpose}-messages")
    return render(request, "clients/messages/delete_message.html")