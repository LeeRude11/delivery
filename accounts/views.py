from django.views.generic import base, edit
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

from .forms import UserCreationForm, CustomAuthForm
SUCCESS_REG_REDIRECT = 'accounts:profile'


class ProfileView(LoginRequiredMixin, base.TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        # TODO a lot more information
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['username'] = user.get_short_name()
        return context


class CustomPasswordChangeView(auth.views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')


class RegisterView(edit.CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    # TODO login automatically
    success_url = reverse_lazy('accounts:login')


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
