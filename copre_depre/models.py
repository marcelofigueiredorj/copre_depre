from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User

class Composicao(models.Model):
    solicitante = models.CharField(max_length=100)
    autor = models.CharField(max_length=100)
    unidade = models.CharField(max_length=50)
    data = models.DateField()  # Alterado para DateField
    codigo = models.CharField(max_length=50)
    numero = models.CharField(max_length=11)
    obra = models.CharField(max_length=255)
    descricao = models.TextField()
    io = models.DateField()  # Alterado para DateField
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

    def calculate_valor_total(self):
        total = sum(
            Decimal(ci.quantidade) * Decimal(ci.valor)
            for ci in self.composicaoinsumo_set.all()
            if ci.quantidade is not None and ci.valor is not None
        )
        self.valor_total = total
        self.save()

class Insumo(models.Model):
    insumo = models.CharField(max_length=255)
    codigo = models.CharField(max_length=50, unique=True)
    unidade = models.CharField(max_length=10)
    data_custo = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.insumo

class ComposicaoInsumo(models.Model):
    composicao = models.ForeignKey(Composicao, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    codigo = models.CharField(max_length=50, blank=True)  # Novo campo
    un = models.CharField(max_length=10, blank=True)      # Novo campo
    data_custo = models.DateField(null=True, blank=True)  # Novo campo
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Novo campo

    def __str__(self):
        return f"{self.insumo} ({self.quantidade})"