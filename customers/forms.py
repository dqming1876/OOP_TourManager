from catalog.forms import BootstrapModelForm

from .models import Customer


class CustomerForm(BootstrapModelForm):
    class Meta:
        model = Customer
        fields = ("full_name", "phone", "email", "id_number", "address", "note")
