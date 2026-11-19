from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("users/<int:pk>/approve/", views.UserApproveView.as_view(), name="user_approve"),
    path("users/<int:pk>/password-reset/", views.UserPasswordResetView.as_view(), name="user_password_reset"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("password-change/", views.SelfPasswordChangeView.as_view(), name="password_change"),
]
