from getpass import getpass
from pathlib import Path

from decouple import Config, RepositoryEnv
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from accounts.services import save_user_account


class Command(BaseCommand):
    help = "Tạo hoặc cập nhật superuser thuộc đúng nhóm Admin; không in mật khẩu."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--email")
        parser.add_argument("--password")

    def handle(self, *args, **options):
        env_file = Path(settings.BASE_DIR) / ".env"
        env = Config(RepositoryEnv(str(env_file))) if env_file.exists() else Config()
        username = options["username"] or env("ADMIN_USERNAME", default="admin") or "admin"
        email = options["email"] if options["email"] is not None else env("ADMIN_EMAIL", default="")
        password = options["password"] if options["password"] is not None else env("ADMIN_PASSWORD", default="")
        if not password:
            try:
                password = getpass("Nhập mật khẩu Admin: ")
                confirmation = getpass("Nhập lại mật khẩu Admin: ")
            except (EOFError, KeyboardInterrupt) as exc:
                raise CommandError("Không đọc được mật khẩu. Hãy cấu hình ADMIN_PASSWORD hoặc nhập trực tiếp tại terminal.") from exc
            if password != confirmation:
                raise CommandError("Hai mật khẩu không khớp.")
        User = get_user_model()
        username = User.normalize_username(username)
        try:
            User._meta.get_field("username").clean(username, None)
            User._meta.get_field("email").clean(email, None)
            user = User.objects.filter(username=username).first() or User(username=username)
            user.email = email
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        if not Group.objects.filter(name="Admin").exists():
            call_command("setup_roles", stdout=self.stdout)
        created = user.pk is None
        try:
            save_user_account(user, Group.objects.get(name="Admin"), True, email=email, password=password, force_superuser=True)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        action = "Tạo mới" if created else "Cập nhật"
        self.stdout.write(self.style.SUCCESS(f"{action} tài khoản Admin {username} thành công."))
