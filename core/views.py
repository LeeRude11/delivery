from django.shortcuts import render, get_object_or_404
from django.views import generic

from .models import InfoViewTemplate


def index(request):
    """
    Index page.
    """
    template_name = 'core/index.html'
    return render(request, template_name)


class InfoView(generic.DetailView):
    template_name = 'core/info.html'
    model = InfoViewTemplate

    def get_object(self):
        view_name = self.kwargs['view_name']
        return get_object_or_404(InfoViewTemplate, view_name=view_name)
