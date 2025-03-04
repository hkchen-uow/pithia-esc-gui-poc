from django.urls import path

from . import views

app_name = 'register'
urlpatterns = [
    path('', views.index, name='index'),
    path('organisation/', views.organisation.as_view(), name='organisation'),
    path('individual/', views.individual.as_view(), name='individual'),
    path('project/', views.project.as_view(), name='project'),
    path('platform/', views.platform.as_view(), name='platform'),
    path('instrument/', views.instrument.as_view(), name='instrument'),
    path('operation/', views.operation.as_view(), name='operation'),
    path('acquisition/', views.acquisition.as_view(), name='acquisition'),
    path('computation/', views.computation.as_view(), name='computation'),
    path('process/', views.process.as_view(), name='process'),
    path('data-collection/', views.data_collection.as_view(), name='data_collection'),
]