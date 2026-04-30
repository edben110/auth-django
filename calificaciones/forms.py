from django import forms
from .models import Calificacion


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['nombre_estudiante', 'identificacion', 'asignatura', 'nota1', 'nota2', 'nota3']
        widgets = {
            'nombre_estudiante': forms.TextInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'asignatura': forms.TextInput(attrs={'class': 'form-control'}),
            'nota1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nota2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nota3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
