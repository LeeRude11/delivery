from django.urls import reverse

from .models import InfoViewTemplate


def info_views_processor(request):
    info_views = InfoViewTemplate.objects.all()
    return {'info_views': info_views}


def navbar_views_processor(request):
    info_views = InfoViewTemplate.objects.all()

    menu_views = [
        {
            'title': 'Specials',
            'url': reverse('menu:specials')
        },
        {
            'title': 'Menu',
            'url': reverse('menu:menu')
        },
    ]

    for view in info_views:
        menu_views.append({
            'title': view.title,
            'url': reverse('core:info', args=(view.view_name,))
        })
    return {'navbar_views': menu_views}
