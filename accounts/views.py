from django.views.generic import base
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


class ProfileView(base.TemplateView):
    template_name = 'registration/profile.html'

    # TODO login_required
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['username'] = user.username
        return context


class CustomPasswordChangeView(auth_views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')
