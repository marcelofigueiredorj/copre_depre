# copre_depre/management/commands/createsu.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Cria um superusuário automaticamente a partir de variáveis de ambiente"

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER", "").lower() != "true":
            self.stdout.write("Variável CREATE_SUPERUSER não é 'true'. Pulando criação do superusuário.")
            return

        username = os.environ.get("admin")
        email = os.environ.get("marcelotechsg@gmail.com")
        password = os.environ.get("filipe98")

        if not username or not email or not password:
            self.stderr.write("Variáveis de ambiente incompletas. Abortando.")
            return

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Usuário '{username}' já existe. Nenhuma ação tomada.")
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"Superusuário '{username}' criado com sucesso.")
