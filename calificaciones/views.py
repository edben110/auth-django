from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Calificacion
from .forms import CalificacionForm


@login_required
def listar(request):
    """Lista todas las calificaciones y calcula el promedio general."""
    calificaciones = Calificacion.objects.all()
    promedio_general = calificaciones.aggregate(Avg('promedio'))['promedio__avg']
    return render(request, 'calificaciones/listar.html', {
        'calificaciones': calificaciones,
        'promedio_general': promedio_general,
    })


@login_required
def crear(request):
    """Crea una calificacion nueva a partir del formulario."""
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar')
    else:
        form = CalificacionForm()
    return render(request, 'calificaciones/crear.html', {'form': form})


@login_required
def editar(request, pk):
    """Edita una calificacion existente identificada por su llave primaria."""
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=calificacion)
        if form.is_valid():
            form.save()
            return redirect('listar')
    else:
        form = CalificacionForm(instance=calificacion)
    return render(request, 'calificaciones/editar.html', {'form': form, 'calificacion': calificacion})


@login_required
def eliminar(request, pk):
    """Confirma y elimina una calificacion existente."""
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if request.method == 'POST':
        calificacion.delete()
        return redirect('listar')
    return render(request, 'calificaciones/eliminar.html', {'calificacion': calificacion})


@login_required
def promedio_general(request):
    """Muestra solamente el promedio general de todas las calificaciones."""
    promedio = Calificacion.objects.all().aggregate(Avg('promedio'))['promedio__avg']
    return render(request, 'calificaciones/promedio_general.html', {'promedio_general': promedio})
