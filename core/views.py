from django.shortcuts import render


def index(request):
    """
    Index page.
    """
    template_name = 'index.html'
    return render(request, template_name)


def delivery(request):
    """
    Info about delivery services.
    """
    template_name = 'delivery.html'
    return render(request, template_name)


def info(request):
    """
    Information about the company.
    """
    template_name = 'info.html'
    return render(request, template_name)


def contacts(request):
    """
    Company contacts page.
    """
    template_name = 'contacts.html'
    return render(request, template_name)
