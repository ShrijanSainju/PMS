from django import forms

class VehicleEntryForm(forms.Form):
    vehicle_number = forms.CharField(label='Vehicle Number', max_length=20)
