from django.contrib import admin
from django.urls import path

from fire.views import (HomePageView, ChartView, PieCountbySeverity, LineCountbyMonth, MultilineIncidentTop3Country, multipleBarbySeverity, 
FireStationListView, FireStationCreateView, FireStationUpdateView, FireStationDeleteView,

)

from fire import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', HomePageView.as_view(), name='home'),
    path('dashboard_chart', ChartView.as_view(), name='dashboard-chart'),
    path('chart/', views.PieCountbySeverity, name='chart'),
    path('lineChart/', views.LineCountbyMonth, name='chart'),
    path('multilineChart/', views.MultilineIncidentTop3Country, name='chart'),
    path('multiBarChart/', views.multipleBarbySeverity, name='chart'),
    path('station', views.map_station, name='map-station'),
    path('incident', views.map_incident, name='map-incident'),

    path('fire_station_list', FireStationListView.as_view(), name='fire-station-list'),
    path('fire_station_list/add', FireStationCreateView.as_view(), name='fire-station-add'),
    path('fire_station_list/<pk>', FireStationUpdateView.as_view(), name='fire-station-update'),
    path('fire_station_list/<pk>/delete', FireStationDeleteView.as_view(), name='fire-station-delete'),
]
