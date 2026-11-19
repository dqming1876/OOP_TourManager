from catalog.crud import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView, paginate_related

from .forms import CustomerForm
from .models import Customer


class CustomerConfig:
    model = Customer
    form_class = CustomerForm
    route_prefix = "customers:customer"
    allowed_roles = ("Sales",)
    manager_roles = ("Sales",)
    search_fields = ("full_name", "phone", "email", "id_number", "address")
    list_fields = ("full_name", "phone", "email", "address")


class CustomerListView(CustomerConfig, EntityListView):
    template_name = "customers/customer_list.html"


class CustomerDetailView(CustomerConfig, EntityDetailView):
    template_name = "customers/customer_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = self.object.bookings.select_related("customer", "departure__tour")
        context["bookings"] = paginate_related(context, bookings, self.request)
        return context


class CustomerCreateView(CustomerConfig, EntityCreateView):
    template_name = "customers/customer_form.html"


class CustomerUpdateView(CustomerConfig, EntityUpdateView):
    template_name = "customers/customer_form.html"


class CustomerDeleteView(CustomerConfig, EntityDeleteView):
    template_name = "customers/customer_confirm_delete.html"
