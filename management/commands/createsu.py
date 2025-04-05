from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Cria um superusuário automaticamente usando variáveis de ambiente'

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER", "").lower() != "true":
            self.stdout.write("Variável CREATE_SUPERUSER não é 'true', pulando criação.")
            return

        User = get_user_model()
        username = os.environ["marcelo"]
        email = os.environ["marcelotechsg@gmail.com"]
        password = os.environ["filipe98"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superusuário '{username}' já existe.")
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"Superusuário '{username}' criado com sucesso.")
