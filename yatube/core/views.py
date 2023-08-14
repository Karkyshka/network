

from django.shortcuts import render


def page_not_found(request, exception):
    data = {'path': request.path}
    return render(request, 'core/404.html', data, status=404)


def csrf_failure(request, reason=''):
    return render(request, 'core/403.html')
