from .models import InfoViewTemplate


def info_views_processor(request):
    info_views = InfoViewTemplate.objects.all()
    return {'info_views': info_views}
