from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from core.forms import LoginForm, RegisterForm, ProfileForm
from core.models import Profile


def _safe_next(request, fallback='index'):
    """Безопасный редирект по параметру next (защита от open redirect)."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(reverse(fallback))


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user:
                auth.login(request, user)
                return _safe_next(request)
            else:
                form.add_error(None, 'Неверный логин или пароль')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    auth.logout(request)
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}
    ):
        return HttpResponseRedirect(referer)
    return HttpResponseRedirect(reverse('index'))


def signup(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = RegisterForm()
    return render(request, 'core/signup.html', {'form': form})


@login_required(login_url=reverse_lazy('login'))
def profile(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile, user=request.user)
        if form.is_valid():
            form.save()
            form = ProfileForm(instance=user_profile, user=request.user)  # обновляем форму
    else:
        form = ProfileForm(instance=user_profile, user=request.user)

    return render(request, 'core/profile.html', {'form': form})
