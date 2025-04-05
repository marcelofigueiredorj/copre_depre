# copre_depre/apps.py
#from django.apps import AppConfig

#class CopreDepreConfig(AppConfig):
#    default_auto_field = 'django.db.models.BigAutoField'
 #   name = 'copre_depre'

from django.apps import AppConfig
from django.db.models.signals import post_migrate
import os

class CopreDepreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'copre_depre'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db import connection

        def create_superuser(sender, **kwargs):
            if os.environ.get("CREATE_SUPERUSER", "").lower() != "true":
                return

            username = os.environ.get("admin", "").strip()
            email = os.environ.get("marcelotechsg@gmail.com", "").strip()
            password = os.environ.get("filipe98", "").strip()

            if not username or not email or not password:
                print("❌ Variáveis de ambiente incompletas. Abortando criação do superusuário.")
                return

            User = get_user_model()

            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                print(f"✅ Superusuário '{username}' criado com sucesso.")
            else:
                print(f"ℹ️ Superusuário '{username}' já existe.")

        post_migrate.connect(create_superuser, sender=self)
