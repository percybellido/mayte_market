from django import forms
# local
from .models import Producto, Categoria


class ProductForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Seleccione una categoría'
    )

    class Meta:
        model = Producto
        fields = (
            'nombre',
            'categoria',
            'descripcion',
            'unidad',
            'cantidad',
            'precio_compra',
            'precio_venta',
            'image',
            'visible_en_tienda',
            'disponible',
            'es_nuevo',
            'en_oferta',
        )
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre...',
                'class': 'form-control',
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Descripción del producto',
                'rows': '3',
                'class': 'form-control',
            }),
            'unidad': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={
                'step': '0.01',  # ✅ permite hasta 2 decimales
                'class': 'form-control',
                'placeholder': 'Cantidad (ej. 2.50)',
            }),
            'precio_compra': forms.NumberInput(attrs={
                'step': '0.01',  # ✅ dos decimales
                'class': 'form-control',
                'placeholder': 'Precio de compra (ej. 12.50)',
            }),
            'precio_venta': forms.NumberInput(attrs={
                'step': '0.01',  # ✅ dos decimales
                'class': 'form-control',
                'placeholder': 'Precio de venta (ej. 15.90)',
            }),
        }

    # ✅ Limpieza para aceptar coma o punto decimal en campos numéricos
    def clean_cantidad(self):
        valor = str(self.cleaned_data['cantidad']).replace(',', '.')
        return float(valor)

    def clean_precio_compra(self):
        valor = str(self.cleaned_data['precio_compra']).replace(',', '.')
        valor = float(valor)
        if valor <= 0:
            raise forms.ValidationError('Ingrese un precio de compra mayor a cero.')
        return valor

    def clean_precio_venta(self):
        valor = str(self.cleaned_data['precio_venta']).replace(',', '.')
        valor = float(valor)
        precio_compra = float(str(self.cleaned_data.get('precio_compra')).replace(',', '.'))
        if valor < precio_compra:
            raise forms.ValidationError('El precio de venta debe ser mayor o igual que el precio de compra.')
        return valor
