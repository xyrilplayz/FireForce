from django.contrib import admin
from django.urls import path

from fire.views import (HomePageView, ChartView, PieCountbySeverity, LineCountbyMonth, MultilineIncidentTop3Country, multipleBarbySeverity, 
LocationListView, LocationCreateView, LocationUpdateView, LocationDeleteView,
IncidentListView, IncidentCreateView, IncidentUpdateView, IncidentDeleteView,
FireStationListView, FireStationCreateView, FireStationUpdateView, FireStationDeleteView,
FirefighterListView, FirefighterCreateView, FirefighterUpdateView, FirefighterDeleteView, WeatherListView, WeatherConditionsCreateView, WeatherConditionsUpdateView, WeatherConditionsDeleteView, DashboardView
)

from fire import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('dashboard_chart', ChartView.as_view(), name='dashboard-chart'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('chart/', views.PieCountbySeverity, name='chart'),
    path('lineChart/', views.LineCountbyMonth, name='chart'),
    path('multilineChart/', views.MultilineIncidentTop3Country, name='chart'),
    path('multiBarChart/', views.multipleBarbySeverity, name='chart'),
    path('station', views.map_station, name='map-station'),
    path('incident', views.map_incident, name='map-incident'),

    path('location_list', LocationListView.as_view(), name='location-list'),
    path('location_list/add', LocationCreateView.as_view(), name='location-add'),
    path('location_list/<pk>', LocationUpdateView.as_view(), name='location-update'),
    path('location_list/<pk>/delete', LocationDeleteView.as_view(), name='location-delete'),

    path('incident_list', IncidentListView.as_view(), name='incident-list'),
    path('incident_list/add', IncidentCreateView.as_view(), name='incident-add'),
    path('incident_list/<pk>', IncidentUpdateView.as_view(), name='incident-update'),
    path('incident_list/<pk>/delete', IncidentDeleteView.as_view(), name='incident-delete'),

    path('fire_station_list', FireStationListView.as_view(), name='fire-station-list'),
    path('fire_station_list/add', FireStationCreateView.as_view(), name='fire-station-add'),
    path('fire_station_list/<pk>', FireStationUpdateView.as_view(), name='fire-station-update'),
    path('fire_station_list/<pk>/delete', FireStationDeleteView.as_view(), name='fire-station-delete'),

    path('firefighter_list', FirefighterListView.as_view(), name='firefighter-list'),
    path('firefighter_list/add', FirefighterCreateView.as_view(), name='firefighter-add'),
    path('firefighter_list/<pk>', FirefighterUpdateView.as_view(), name='firefighter-update'),
    path('firefighter_list/<pk>/delete', FirefighterDeleteView.as_view(), name='firefighter-delete'),

    path('weather_list', WeatherListView.as_view(), name='weather-list'),
    path('weather_add', WeatherConditionsCreateView.as_view(), name='weather-station-add'),
    path('weather_list/<pk>', WeatherConditionsUpdateView.as_view(), name='weather-update'),
    path('weather_list/<pk>/delete', WeatherConditionsDeleteView.as_view(), name='firefighter-delete'),
]