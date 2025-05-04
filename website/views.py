from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from website.models import (
    UnitListing,
    Lister,
    UnitAmenity,
    ListingImage,
    ListingInterestExpression,
    ClientRequest,
    UploadedImage,
)


# Create your views here.
class ListingListView(ListView):
    model = UnitListing
    template_name = "website/listings.html"
    context_object_name = "listings"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(town__icontains=search_query)
                | Q(county__icontains=search_query)
                | Q(unit_type__icontains=search_query)
                | Q(listing_type__icontains=search_query)
                | Q(property_name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def unit_listing_details(request, pk):
    listing = UnitListing.objects.get(pk=pk)
    amenities = listing.amenities.all()
    interests = listing.listinginterests.all().order_by("-created_at")

    total_leads = listing.listinginterests.all().count()

    context = {
        "listing": listing,
        "amenities": amenities,
        "interests": interests,
        "total_leads": total_leads,
    }

    return render(request, "website/listing_details.html", context)


def approve_listing(request):
    if request.method == "POST":
        listing_id = request.POST.get("listing_id")
        listing = UnitListing.objects.get(id=listing_id)
        listing.approved = True
        listing.save()
        return redirect("listing-details", pk=listing_id)
    return render(request, "website/approve_listing.html")


def reject_listing(request):
    if request.method == "POST":
        listing_id = request.POST.get("listing_id")
        listing = UnitListing.objects.get(id=listing_id)
        listing.approved = False
        listing.save()
        return redirect("listing-details", pk=listing_id)
    return render(request, "website/decline_listing.html")


@login_required
@transaction.atomic
def new_webiste_listing(request):
    if request.method == "POST":
        unit_image = request.FILES.get("unit_image")

        new_listing = UnitListing.objects.create(
            property_name=request.POST.get("property_name"),
            listing_type=request.POST.get("listing_type"),
            unit_type=request.POST.get("unit_type"),
            listing_purpose=request.POST.get("listing_purpose"),
            town=request.POST.get("town"),
            county=request.POST.get("county"),
            location_description=request.POST.get("location_description"),
            unit_price=request.POST.get("unit_price"),
            total_units=request.POST.get("total_units"),
            smoking_allowed=request.POST.get("smoking_allowed"),
            pets_allowed=request.POST.get("pets_allowed"),
            bathrooms=request.POST.get("bathrooms"),
            security_deposit=request.POST.get("security_deposit"),
            parking_available=request.POST.get("parking_available"),
            notice_period=request.POST.get("notice_period"),
            minimum_lease_period=request.POST.get("minimum_lease_period"),
            unit_status="Available",
            unit_image=unit_image,
        )

        ListingImage.objects.create(listing=new_listing, image=unit_image)
        amenities_list = [
            "Power Backup",
            "Water Backup",
            "Internet",
            "Gym",
            "Swimming Pool",
            "Kids Playground",
            "Security",
            "Parking",
            "Garbage Disposal",
            "Gas",
            "Laundry",
            "Wheelchair Access",
            "Elevator",
            "24hr Security",
            "24hr Water Supply",
            "CCTV",
            "Security Guard",
            "House Keeping",
            "Maintenance",
            "Backyard",
            "Balcony",
            "Garden",
            "Rooftop Access",
        ]
        listing_amenities = []

        for amenity in amenities_list:
            listing_amenities.append(
                UnitAmenity(unit_listing=new_listing, name=amenity)
            )
        UnitAmenity.objects.bulk_create(listing_amenities)

        return render(request, "website/new_listing.html")


def mark_amenity_available(request, id):
    amenity = UnitAmenity.objects.get(id=id)
    amenity.available = True
    amenity.save()
    return redirect("listing-details", pk=amenity.unit_listing.id)


def mark_amenity_unavailable(request, id):
    amenity = UnitAmenity.objects.get(id=id)
    amenity.available = False
    amenity.save()
    return redirect("listing-details", pk=amenity.unit_listing.id)


class InterestExpressionListView(ListView):
    model = ListingInterestExpression
    template_name = "website/interests/interests.html"
    context_object_name = "interests"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(property_name__icontains=search_query)
                | Q(name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ListerView(ListView):
    model = Lister
    template_name = "website/listers/listers.html"
    context_object_name = "listers"

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get("search", "")
        print(f"You are searching for: {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@ensure_csrf_cookie
@require_http_methods(["POST"])
def upload_images(request):
    try:
        # Get the uploaded files
        files = request.FILES.getlist("images")

        if not files:
            return JsonResponse(
                {"status": "error", "message": "No files were uploaded"}, status=400
            )

        uploaded_images = []

        # Process each uploaded file
        for file in files:
            # Validate file type
            if not file.content_type.startswith("image/"):
                continue

            # Validate file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                continue

            # Save the image
            image = UploadedImage(image=file)
            image.save()

            uploaded_images.append(
                {
                    "id": image.id,
                    "url": image.image.url,
                    "uploaded_at": image.uploaded_at.isoformat(),
                }
            )

        if not uploaded_images:
            return JsonResponse(
                {"status": "error", "message": "No valid images were uploaded"},
                status=400,
            )

        return JsonResponse(
            {
                "status": "success",
                "message": f"Successfully uploaded {len(uploaded_images)} images",
                "images": uploaded_images,
            }
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
