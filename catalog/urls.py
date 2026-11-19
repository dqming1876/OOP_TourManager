from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/create/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("suppliers/<int:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("suppliers/<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier_update"),
    path("suppliers/<int:pk>/delete/", views.SupplierDeleteView.as_view(), name="supplier_delete"),
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path("services/create/", views.ServiceCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service_update"),
    path("services/<int:pk>/delete/", views.ServiceDeleteView.as_view(), name="service_delete"),
    path("guides/", views.GuideListView.as_view(), name="guide_list"),
    path("guides/create/", views.GuideCreateView.as_view(), name="guide_create"),
    path("guides/<int:pk>/", views.GuideDetailView.as_view(), name="guide_detail"),
    path("guides/<int:pk>/edit/", views.GuideUpdateView.as_view(), name="guide_update"),
    path("guides/<int:pk>/delete/", views.GuideDeleteView.as_view(), name="guide_delete"),
    path("vehicles/", views.VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", views.VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<int:pk>/", views.VehicleDetailView.as_view(), name="vehicle_detail"),
    path("vehicles/<int:pk>/edit/", views.VehicleUpdateView.as_view(), name="vehicle_update"),
    path("vehicles/<int:pk>/delete/", views.VehicleDeleteView.as_view(), name="vehicle_delete"),
    path("tours/", views.TourListView.as_view(), name="tour_list"),
    path("tours/create/", views.TourCreateView.as_view(), name="tour_create"),
    path("tours/<int:pk>/", views.TourDetailView.as_view(), name="tour_detail"),
    path("tours/<int:pk>/edit/", views.TourUpdateView.as_view(), name="tour_update"),
    path("tours/<int:pk>/delete/", views.TourDeleteView.as_view(), name="tour_delete"),
    path("departures/", views.DepartureListView.as_view(), name="departure_list"),
    path("departures/create/", views.DepartureCreateView.as_view(), name="departure_create"),
    path("departures/<int:pk>/", views.DepartureDetailView.as_view(), name="departure_detail"),
    path("departures/<int:pk>/edit/", views.DepartureUpdateView.as_view(), name="departure_update"),
    path("departures/<int:pk>/delete/", views.DepartureDeleteView.as_view(), name="departure_delete"),
]
