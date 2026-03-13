from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации пользователя с выбором роли.
    Наследует логику UserCreationForm, но работает с CustomUser.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'role', 'password1', 'password2')

class JoinSessionForm(forms.Form):
    """
    Простая форма для ввода кода сессии кандидатом.
    """
    code = forms.CharField(
        max_length=8,
        label='Код сессии',
        widget=forms.TextInput(attrs={'placeholder': 'Ваш код приглашения'})
    )
