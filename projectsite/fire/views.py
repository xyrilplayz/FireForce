from django.shortcuts import render
from django.views.generic.list import ListView
from fire.models import Locations, Incident, FireStation

class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"

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
    incidents = Incident.objects.select_related('location').all()
    incident_list = []
    for incident in incidents:
        location = incident.location
        incident_data = {
            'name': incident.location.name,
            'latitude': float(location.latitude) if location.latitude else None,
            'longitude': float(location.longitude) if location.longitude else None,
            'address': location.address,
            'city': location.city,
            'country': location.country,
            'date_time': incident.date_time.strftime("%Y-%m-%d %H:%M:%S") if incident.date_time else '',
            'severity_level': incident.severity_level,
            'description': incident.description
        }
        incident_list.append(incident_data)

    context = {
        'incidents': incident_list
    }
    return render(request, 'map_incident.html', context)