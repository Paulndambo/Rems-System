from django.contrib import admin

from website.models import (
    ClientRequest,
    ListingInterestExpression,
    Subscription,
    Lister,
    ListingImage,
    ListingCity,
)


# Register your models here.
@admin.register(ClientRequest)
class ClientRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "property_type",
        "unit_type",
        "phone",
        "email",
        "budget",
    ]


@admin.register(ListingInterestExpression)
class ListingInterestExpressionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "listing",
        "preferredContact",
        "phone",
        "email",
        "processed",
    ]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "cost", "currency", "is_public", "is_active"]


@admin.register(Lister)
class ListerAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "lister_type", "subscription"]


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "listing", "image", "image_url"]


@admin.register(ListingCity)
class ListingCityAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "county", "cover_image"]
