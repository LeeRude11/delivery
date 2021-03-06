from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

from .forms import UserCreationForm, UserUpdateForm, CustomAuthForm
SUCCESS_REG_REDIRECT = 'accounts:profile'


@login_required
def profile(request):
    """
    Render a populated form with user's info, which can be updated.
    """
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'registration/profile.html', {'form': form})


class CustomPasswordChangeView(auth.views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')


def registration(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('phone_number')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(SUCCESS_REG_REDIRECT)
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


class CustomLoginView(auth.views.LoginView):
    form_class = CustomAuthForm
