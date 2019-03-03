from django.views.generic import base, edit
from django.contrib import auth
from django.urls import reverse_lazy

from .forms import UserCreationForm


class ProfileView(base.TemplateView):
    template_name = 'registration/profile.html'

    # TODO login_required
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
