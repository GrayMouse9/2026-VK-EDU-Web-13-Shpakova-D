from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.models import Profile


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'})
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirmation = forms.CharField(
        label='Подтвердите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Логин',
            'email': 'Email',
            'first_name': 'Имя',
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')

        if password and password_confirmation and password != password_confirmation:
            raise ValidationError('Пароли не совпадают')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Profile.objects.create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='NickName',
        required=False, # Делаем необязательным, вдруг юзер захочет стереть ник
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Profile
        fields = ('avatar',)
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'avatar': 'Аватар',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            if commit:
                self.user.save()
                profile.user = self.user
                profile.save()
        return profile
