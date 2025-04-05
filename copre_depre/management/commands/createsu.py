from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Cria um superusuário automaticamente a partir de variáveis de ambiente"

    def handle(self, *args, **options):
        print("DEBUG VARIÁVEIS:")
        username = os.environ.get("admin", "").strip()
        email = os.environ.get("marcelotachsg@gmail.com", "").strip()
        password = os.environ.get("filipe98", "").strip()
        create = os.environ.get("CREATE_SUPERUSER", "").strip().lower()

        print("USERNAME:", username)
        print("EMAIL:", email)
        print("PASSWORD:", "*" * len(password))  # não mostra a senha nos logs

        if create != "true":
            self.stdout.write("CREATE_SUPERUSER não é 'true'. Pulando criação.")
            return

        if not username or not email or not password:
            self.stderr.write("❌ Variáveis de ambiente incompletas. Abortando.")
            return

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"✅ Superusuário '{username}' já existe. Nenhuma ação tomada.")
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"✅ Superusuário '{username}' criado com sucesso.")
