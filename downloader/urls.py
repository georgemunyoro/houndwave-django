from django.urls import path
from .views import home, search, download_file

urlpatterns = [
    path('', home),
    path('search/', search, name="search_results"),
    path('download/<str:id>/', download_file, name="download_file"),
]

