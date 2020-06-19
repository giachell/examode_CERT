"""examodeWebAppInstance URL Configuration

Defines URL patterns for 'examodeWebAppInstance' app of ''examodeWebApp' project
"""

from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name ='examodeWebAppInstance'

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('getReport', views.getReport, name='getReport'),
    path('download', views.download, name='download'),
    path('/', views.index, name='index'),
    path('/index', views.index, name='index'),
    path('/getReport', views.getReport, name='getReport'),
    path('/download/<filename>', views.download, name='download'),
    path('/spellchecker/<word>', views.spellchecker, name='spellchecker'),
    path('/static/<dir>/<file>', views.static, name='static'),
]
