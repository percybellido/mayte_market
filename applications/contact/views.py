from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from .forms import ContactForm

def contact(request):
    contact_form = ContactForm()

    if request.method == "POST":
        contact_form = ContactForm(data=request.POST)
        if contact_form.is_valid():
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            content = request.POST.get('content', '')

            email_from = settings.EMAIL_HOST_USER
            recipient_list = ["pbellido0401@gmail.com"]

            try:
                send_mail(
                    subject=f"Mensaje de {name} ({email})",
                    message=content,
                    from_email=email_from,
                    recipient_list=recipient_list
                )
                messages.success(request, "✅ Tu mensaje fue enviado exitosamente.")
                return redirect(reverse('contact_app:contact'))
            except BadHeaderError:
                messages.error(request, "❌ Hubo un problema con el encabezado del correo.")
            except Exception as e:
                messages.error(request, f"❌ No se pudo enviar el mensaje: {str(e)}")

    return render(request, "contact/contacto.html", {'form': contact_form})
