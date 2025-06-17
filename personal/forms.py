from django import forms

class VehicleEntryForm(forms.Form):
    vehicle_number = forms.CharField(label="Vehicle Number", max_length=20)

class LookupForm(forms.Form):
    vehicle_number = forms.CharField(label="Enter Your Vehicle Number", max_length=20)
