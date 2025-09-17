from django import forms
from applications.product.models import Producto
from applications.customers.models import Cliente
from .models import Pago, MetodosPago
from .models import Venta

class VentaForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label='Cliente',
        widget=forms.Select(attrs={
            'class': 'form-control select-cliente',
        })
    )
    
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        label='Producto',
        widget=forms.Select(attrs={
            'class': 'form-control select-producto',
        })
    )
    
    cantidad = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'placeholder': 'Cantidad'
        })
    )

    def clean_cantidad(self):
        cantidad = self.cleaned_data['cantidad']
        if cantidad < 1:
            raise forms.ValidationError('Ingrese una cantidad mayor a cero')
        return cantidad

    
class PagoForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    total_pagado = forms.DecimalField(
        label="Monto del Pago",
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodosPago.objects.all(),
        label="Método de Pago",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class AbonoForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Monto a abonar",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese monto del abono'
        })
    )
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodosPago.objects.all(),
        label="Método de Pago",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
