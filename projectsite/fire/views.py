from django.shortcuts import render
from django.views.generic.list import ListView 
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from fire.models import Locations, Incident, FireStation, Firefighters, WeatherConditions
from fire.forms import LocationsForm, IncidentForm, FireStationForm, FirefightersForm, WeatherConditionsForm
from django.urls import reverse_lazy
from django.contrib import messages

from django.db.models import Q
import json

from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth

from django.db.models import Count
from datetime import datetime

class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"

class ChartView(ListView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def get_queryset(self):
        pass

def PieCountbySeverity(request):
    query = '''
    SELECT severity_level, COUNT(*) as count
    FROM fire_incident
    GROUP BY severity_level
    '''
    data = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    if rows:
        # Construct the dictionary with severity levels as keys and counts as values
        data = {severity: count for severity, count in rows}
    else:
        data = {}

    return JsonResponse(data)

def LineCountbyMonth(request):

    current_year = datetime.now().year

    result = {month: 0 for month in range(1, 13)}

    incidents_per_month = Incident.objects.filter(date_time__year=current_year) \
        .values_list('date_time', flat=True)
    
    # Count the number of incidents per month
    for date_time in incidents_per_month:
        month = date_time.month
        result[month] += 1

    # Convert numbers to month names
    month_names = {
        1: 'Jan',
        2: 'Feb',
        3: 'Mar',
        4: 'Apr',
        5: 'May',
        6: 'Jun',
        7: 'Jul',
        8: 'Aug',
        9: 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dec'
    }

    result_with_month_names = {
        month_names[int(month)]: count for month, count in result.items()}
    
    return JsonResponse(result_with_month_names)

def MultilineIncidentTop3Country(request):

    query = '''
        SELECT
        fl.country,
        strftime('%m', fi.date_time) AS month,
        COUNT(*) AS incident_count
    FROM
        fire_incident fi
    JOIN
        fire_locations fl ON fi.location_id = fl.id
    WHERE
        fl.country IN (
            SELECT
                fl_top.country
            FROM
                fire_incident fi_top
            JOIN
                fire_locations fl_top ON fi_top.location_id = fl_top.id
            WHERE
                strftime('%Y', fi_top.date_time) = strftime('%Y', 'now')
            GROUP BY
                fl_top.country
            ORDER BY
                COUNT(fi_top.id) DESC
            LIMIT 3
        )
        AND strftime('%Y', fi.date_time) = strftime('%Y', 'now')
    GROUP BY
        fl.country, month
    ORDER BY
        fl.country, month;
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}

    # Initialize a set of months from January to December
    months = set(str(i).zfill(2) for i in range(1, 13))

    # Loop through the query results
    for row in rows:
        country = row[0]
        month = row[1]
        total_incidents = row[2]

        # If the country is not already in the result dictionary, initialize it with all months set to zero
        if country not in result:
            result[country] = {m: 0 for m in months}

        # Update the incident count for the corresponding month
        result[country][month] = total_incidents

    # Ensure there are always 3 countries in the result
    while len(result) < 3:
        missing_country = f"Country {len(result) + 1}"
        result[missing_country] = {m: 0 for m in months}

    for country in result:
            result[country] = dict(sorted(result[country].items()))

    return JsonResponse(result)

def multipleBarbySeverity(request):
    query = '''
    SELECT
        fi.severity_level,
        strftime('%m', fi.date_time) AS month,
        COUNT(fi.id) AS incident_count
    FROM
        fire_incident fi
    GROUP BY fi.severity_level, month;
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}
    months = set(str(i).zfill(2) for i in range(1, 13))

    for row in rows:
        level = str(row[0]) # Ensure the severity level is a string
        month = row[1]
        total_incidents = row[2]

        if level not in result:
            result[level] = {month: 0 for month in months}

        result[level][month] = total_incidents

    # Sort months within each severity level
    for level in result:
        result[level] = dict(sorted(result[level].items()))

    return JsonResponse(result)
    
def map_station(request):
    fireStations = FireStation.objects.values('name', 'latitude', 'longitude')

    for fs in fireStations:
        fs ['latitude'] = float (fs['latitude'])
        fs ['longitude'] = float (fs['longitude'])

    fireStations_list = list(fireStations)

    context = {
        'fireStations': fireStations_list
    }

    return render (request, 'map_station.html', context )

def map_incident(request):
    city_filter = request.GET.get('city')
    incidents_qs = Incident.objects.select_related('location')

    if city_filter:
        incidents_qs = incidents_qs.filter(location__city__iexact=city_filter)

    incident_list = []
    for incident in incidents_qs:
        location = incident.location
        incident_data = {
            'name': location.name,
            'latitude': float(location.latitude) if location.latitude else None,
            'longitude': float(location.longitude) if location.longitude else None,
            'address': location.address,
            'city': location.city,
            'country': location.country,
            'date_time': incident.date_time.strftime("%Y-%m-%d %H:%M:%S") if incident.date_time else '',
            'severity_level': incident.severity_level,
            'description': incident.description
        }
        if incident_data['latitude'] and incident_data['longitude']:
            incident_list.append(incident_data)

    cities = Locations.objects.values_list('city', flat=True).distinct()

    context = {
        'incidents': json.dumps(incident_list),
        'cities': sorted(set(cities)),
        'selected_city': city_filter or ''
    }
    return render(request, 'map_incident.html', context)


class LocationListView(ListView):
    model = Locations
    context_object_name = 'location'
    template_name = "location_list.html"
    paginate_by = 5
    ordering = ['name']

class LocationCreateView(CreateView):
    model = Locations
    form_class = LocationsForm
    template_name = 'location_add.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Location added successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Location was not added!')
        return super().form_invalid(form)
    
class LocationUpdateView(UpdateView):
    model = Locations
    form_class = LocationsForm
    template_name = 'location_edit.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Location updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Location was not updated!')
        return super().form_invalid(form)

class LocationDeleteView(DeleteView):
    model = Locations
    template_name = 'location_del.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Location deleted successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Location was not deleted!')
        return super().form_invalid(form)
    
class IncidentListView(ListView):
    model = Incident
    context_object_name = 'incident'
    template_name = "incident_list.html"
    paginate_by = 5
    ordering = ['date_time']

class IncidentCreateView(CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incident_add.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Incident added successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Incident was not added!')
        return super().form_invalid(form)
    
class IncidentUpdateView(UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incident_edit.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Incident updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Incident was not updated!')
        return super().form_invalid(form)

class IncidentDeleteView(DeleteView):
    model = Incident
    template_name = 'incident_del.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Incident deleted successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Incident was not deleted!')
        return super().form_invalid(form)
    
class FireStationListView(ListView):
    model = FireStation
    context_object_name = 'fire_station'
    template_name = "fire_station_list.html"
    paginate_by = 5
    ordering = ['name']

class FireStationCreateView(CreateView):
    model = FireStation
    form_class = FireStationForm
    template_name = 'fire_station_add.html'
    success_url = reverse_lazy('fire-station-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fire Station added successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Fire Station was not added!')
        return super().form_invalid(form)
    
class FireStationUpdateView(UpdateView):
    model = FireStation
    form_class = FireStationForm
    template_name = 'fire_station_edit.html'
    success_url = reverse_lazy('fire-station-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fire Station updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Fire Station was not updated!')
        return super().form_invalid(form)

class FireStationDeleteView(DeleteView):
    model = FireStation
    template_name = 'fire_station_del.html'
    success_url = reverse_lazy('fire-station-list')
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fire Station deleted successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Fire Station was not deleted!')
        return super().form_invalid(form)
    
class FirefighterListView(ListView):
    model = Firefighters
    context_object_name = 'firefighter'
    template_name = "firefighter_list.html"
    paginate_by = 5
    ordering = ['name']

class FirefighterCreateView(CreateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_add.html'
    success_url = reverse_lazy('firefighter-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Firefighter added successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Firefighter was not added!')
        return super().form_invalid(form)
    
class FirefighterUpdateView(UpdateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_edit.html'
    success_url = reverse_lazy('firefighter-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Firefighter updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Firefighter was not updated!')
        return super().form_invalid(form)

class FirefighterDeleteView(DeleteView):
    model = Firefighters
    template_name = 'firefighter_del.html'
    success_url = reverse_lazy('firefighter-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Firefighter deleted successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Firefighter was not deleted!')
        return super().form_invalid(form)

class WeatherListView(ListView):
    model = WeatherConditions
    context_object_name = 'WeatherConditions'
    template_name = "weather_list.html"
    paginate_by = 5
    ordering = ['incident_id', 'temperature','humidity','wind_speed','weather_description']  

class WeatherConditionsCreateView(CreateView):
    model = WeatherConditions
    form_class = WeatherConditionsForm
    template_name = 'weather_add.html'
    success_url = reverse_lazy('weather-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Weather added successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Weather was not added!')
        return super().form_invalid(form)
    
class WeatherConditionsUpdateView(UpdateView):
    model = WeatherConditions
    form_class = WeatherConditionsForm
    template_name = 'weather_edit.html'
    success_url = reverse_lazy('weather-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Weather updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Weather was not updated!')
        return super().form_invalid(form)
    
class WeatherConditionsDeleteView(DeleteView):
    model = WeatherConditions
    template_name = 'weather_del.html'
    success_url = reverse_lazy('weather-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'weather deleted successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'weather was not deleted!')
        return super().form_invalid(form)