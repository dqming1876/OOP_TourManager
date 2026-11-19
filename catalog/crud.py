"""Các CBV dùng lại cho danh mục và khách hàng, không sửa khung chung."""
from datetime import date, datetime
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.urls import reverse
from django.utils import formats, timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import get_user_roles


def display_value(obj, name):
    value = getattr(obj, name)
    get_label = getattr(obj, f"get_{name}_display", None)
    if get_label:
        return get_label()
    if value is None or value == "":
        return "—"
    if isinstance(value, datetime):
        return formats.date_format(timezone.localtime(value), "d/m/Y H:i")
    if isinstance(value, date):
        return formats.date_format(value, "d/m/Y")
    if isinstance(value, Decimal):
        return formats.number_format(value, decimal_pos=0, force_grouping=True)
    return str(value)


def paginate_related(context, queryset, request):
    page = Paginator(queryset, 10).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    context.update(page_obj=page, paginator=page.paginator, is_paginated=page.has_other_pages(), pagination_query=query.urlencode())
    return page


class EntityContextMixin:
    route_prefix = ""
    manager_roles = ("Operator",)
    list_fields = ()
    detail_fields = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roles = get_user_roles(self.request.user)
        context.update({
            "entity_name": self.model._meta.verbose_name,
            "list_url": reverse(f"{self.route_prefix}_list"),
            "create_url": reverse(f"{self.route_prefix}_create"),
            "can_manage": "Admin" in roles or bool(set(roles).intersection(self.manager_roles)),
            "save_verb": getattr(self, "save_verb", ""),
        })
        obj = getattr(self, "object", None)
        if obj is not None:
            context["detail_url"] = reverse(f"{self.route_prefix}_detail", args=[obj.pk])
            context["update_url"] = reverse(f"{self.route_prefix}_update", args=[obj.pk])
            context["delete_url"] = reverse(f"{self.route_prefix}_delete", args=[obj.pk])
            names = self.detail_fields or tuple(field.name for field in self.model._meta.fields if field.name != "id")
            context["details"] = [(self.model._meta.get_field(name).verbose_name, display_value(obj, name)) for name in names]
        return context


class EntityListView(EntityContextMixin, RoleRequiredMixin, ListView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_list.html"
    paginate_by = 10
    search_fields = ()
    select_related_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(*self.select_related_fields)
        q = self.request.GET.get("q", "").strip()
        if q:
            condition = Q()
            for name in self.search_fields:
                condition |= Q(**{f"{name}__icontains": q})
            queryset = queryset.filter(condition)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context["pagination_query"] = query.urlencode()
        context["q"] = self.request.GET.get("q", "").strip()
        context["headers"] = [self.model._meta.get_field(name).verbose_name for name in self.list_fields]
        context["rows"] = [{
            "values": [display_value(obj, name) for name in self.list_fields],
            "detail_url": reverse(f"{self.route_prefix}_detail", args=[obj.pk]),
            "update_url": reverse(f"{self.route_prefix}_update", args=[obj.pk]),
            "delete_url": reverse(f"{self.route_prefix}_delete", args=[obj.pk]),
        } for obj in context["object_list"]]
        return context


class EntityDetailView(EntityContextMixin, RoleRequiredMixin, DetailView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_detail.html"


class SavedMessageMixin:
    def get_success_url(self):
        return reverse(f"{self.route_prefix}_detail", args=[self.object.pk])

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Đã {self.save_verb.lower()} {self.model._meta.verbose_name.lower()} thành công.")
        return response


class EntityCreateView(EntityContextMixin, RoleRequiredMixin, SavedMessageMixin, CreateView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_form.html"
    save_verb = "Thêm"


class EntityUpdateView(EntityContextMixin, RoleRequiredMixin, SavedMessageMixin, UpdateView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_form.html"
    save_verb = "Cập nhật"


class EntityDeleteView(EntityContextMixin, RoleRequiredMixin, DeleteView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_confirm_delete.html"

    def get_form_class(self):
        # Form xóa chỉ cần xác nhận, không dùng ModelForm của trang thêm/sửa.
        return forms.Form

    def get_success_url(self):
        return reverse(f"{self.route_prefix}_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Không thể xóa vì bản ghi đang được dữ liệu khác tham chiếu. Hãy xử lý dữ liệu liên quan trước.")
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(self.request, f"Đã xóa {self.model._meta.verbose_name.lower()} thành công.")
        return response
