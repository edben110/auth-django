from django.db import models


class Calificacion(models.Model):
    """Representa las notas de un estudiante para una asignatura."""

    nombre_estudiante = models.CharField(max_length=150)
    identificacion = models.CharField(max_length=15)
    asignatura = models.CharField(max_length=100)
    nota1 = models.DecimalField(max_digits=5, decimal_places=2)
    nota2 = models.DecimalField(max_digits=5, decimal_places=2)
    nota3 = models.DecimalField(max_digits=5, decimal_places=2)
    promedio = models.DecimalField(max_digits=5, decimal_places=2, editable=False, default=0)

    def calcular_promedio(self):
        """Calcula el promedio aritmetico de las tres notas registradas."""
        return round((self.nota1 + self.nota2 + self.nota3) / 3, 2)

    def save(self, *args, **kwargs):
        """Actualiza el promedio automaticamente antes de guardar."""
        self.promedio = self.calcular_promedio()
        super().save(*args, **kwargs)

    def __str__(self):
        """Muestra estudiante, asignatura y promedio en admin y consultas."""
        return f"{self.nombre_estudiante} - {self.asignatura} ({self.promedio})"
