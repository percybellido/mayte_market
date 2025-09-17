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
        )
        widgets = {
            'nombre': forms.TextInput(
                attrs = {
                    'placeholder': 'Nombre...',
                    'class': 'form-control',
                }
            ),
             'categoria': forms.Select(
                attrs = {
                    'placeholder': 'Categoria...',
                    'class': 'form-control',
                }
            ),
            
            'descripcion': forms.Textarea(
                attrs = {
                    'placeholder': 'Descripcion del producto',
                    'rows': '3',
                    'class': 'form-control',
                }
            ),
            'unidad': forms.Select(
                attrs = {
                    'class': 'form-control',
                }
            ),
            'cantidad': forms.NumberInput(
                attrs = {
                    'placeholder': 'Codigo de barras',
                    'class': 'form-control',
                }
            ),
            'precio_compra': forms.NumberInput(
                attrs = {
                    'placeholder': '1',
                    'class': 'form-control',
                }
            ),
            'precio_venta': forms.NumberInput(
                attrs = {
                    'placeholder': '1',
                    'class': 'form-control',
                }
            ),
        }
    # validations
    
    
    def clean_precio_compra(self):
        precio_compra = self.cleaned_data['precio_compra']
        if not precio_compra > 0:
            raise forms.ValidationError('Ingrese un precio compra mayor a cero')

        return precio_compra
    
    def clean_precio_venta(self):
        precio_venta = self.cleaned_data['precio_venta']
        precio_compra = self.cleaned_data.get('precio_compra')
        if not precio_venta >= precio_compra:
            raise forms.ValidationError('El precio de venta debe ser mayor o igual que el precio de compra')

        return precio_venta
