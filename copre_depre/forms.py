# copre_depre/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Composicao, Insumo, ComposicaoInsumo  # Removido User daqui
from django.core.exceptions import ValidationError
import datetime

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):  # Alterado de ModelForm para Form simples
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("As senhas não coincidem!")
        return cleaned_data

class ResetPasswordForm(forms.Form):
    username = forms.CharField(max_length=100)

def is_valid_date(date_str):
    if not date_str:
        return True
    try:
        day, month, year = map(int, date_str.split('/'))
        datetime.datetime(year, month, day)
        return 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 9999
    except (ValueError, IndexError):
        return False

class ComposicaoForm(forms.ModelForm):
    class Meta:
        model = Composicao
        fields = ['solicitante', 'autor', 'unidade', 'data', 'codigo', 'numero', 'obra', 'descricao', 'io', 'valor_total']
        widgets = {
            'data': forms.TextInput(attrs={'placeholder': 'DD/MM/AAAA'}),
            'numero': forms.TextInput(attrs={'placeholder': 'XX.XXX.XXX-XX'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'valor_total': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

    def clean_data(self):
        data = self.cleaned_data['data']
        if not is_valid_date(data):
            raise ValidationError("Data inválida (DD/MM/AAAA)")
        return data

    def clean_io(self):
        io = self.cleaned_data['io']
        if not is_valid_date(io):
            raise ValidationError("IO inválida (DD/MM/AAAA)")
        return io

class ComposicaoInsumoForm(forms.ModelForm):
    class Meta:
        model = ComposicaoInsumo
        fields = ['insumo', 'codigo', 'un', 'quantidade', 'data_custo', 'valor']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'step': '0.01'}),
            'data_custo': forms.DateInput(attrs={'placeholder': 'DD/MM/AAAA', 'type': 'text'}),
            'valor': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']
        if quantidade <= 0:
            raise ValidationError("A quantidade deve ser positiva")
        return quantidade

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor < 0:
            raise ValidationError("O valor não pode ser negativo")
        return valor

    def clean_data_custo(self):
        data_custo = self.cleaned_data['data_custo']
        if data_custo and not is_valid_date(data_custo.strftime('%d/%m/%Y')):
            raise ValidationError("Data de custo inválida (DD/MM/AAAA)")
        return data_custo

ComposicaoInsumoFormSet = inlineformset_factory(
    Composicao, ComposicaoInsumo,
    form=ComposicaoInsumoForm,
    fields=['insumo', 'codigo', 'un', 'quantidade', 'data_custo', 'valor'],
    extra=1,
    can_delete=True,
)

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = '__all__'