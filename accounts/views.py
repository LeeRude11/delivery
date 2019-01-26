from django.views.generic import base, edit
from django.contrib import auth
from django.urls import reverse_lazy


class ProfileView(base.TemplateView):
    template_name = 'registration/profile.html'

    # TODO login_required
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['username'] = user.username
        return context


class CustomPasswordChangeView(auth.views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')


class RegisterView(edit.CreateView):
    template_name = 'registration/register.html'
    form_class = auth.forms.UserCreationForm
    # TODO login automatically
    success_url = reverse_lazy('accounts:login')
