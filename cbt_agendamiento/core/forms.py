from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date
from .models import (
    Establecimiento, 
    TipoEstablecimiento, 
    AgendaDiaria, 
    PerfilUsuario, 
    ConfiguracionSistema,
    TasaPago,
    RequisitoLegal
)

# --- 1. CONFIGURACIÓN Y CATÁLOGOS ---

class TipoEstablecimientoForm(forms.ModelForm):
    class Meta:
        model = TipoEstablecimiento
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'EJ: FARMACIA'})
        }

class ConfiguracionGlobalForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSistema
        fields = ['def_capacidad_manana', 'def_capacidad_tarde']
        widgets = {
            'def_capacidad_manana': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'def_capacidad_tarde': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

# --- 2. GESTIÓN DE AGENDA (CORREGIDO AQUÍ) ---

class EdicionAgendaForm(forms.ModelForm):
    class Meta:
        model = AgendaDiaria
        fields = ['capacidad_manana', 'capacidad_tarde', 'cupos_habilitados']
        widgets = {
            'capacidad_manana': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'capacidad_tarde': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            # CAMBIO IMPORTANTE: Agregamos 'peer sr-only' para que funcione el switch de Tailwind
            'cupos_habilitados': forms.CheckboxInput(attrs={'class': 'sr-only peer'}),
        }

# --- 3. GESTIÓN DE USUARIOS Y PERSONAL ---

class NuevoInspectorForm(forms.ModelForm):
    cedula = forms.CharField(label="Cédula (Usuario)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CÉDULA'}))
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    email = forms.EmailField(label="Email Institucional", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['cedula']
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True  # Rol de Inspector
        
        if commit:
            user.save()
            # Perfil básico para inspector
            PerfilUsuario.objects.create(
                user=user,
                ruc="INSTITUCIONAL", 
                telefono=self.cleaned_data['telefono']
            )
        return user

class EditarUsuarioForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    last_name = forms.CharField(label="Apellidos", required=False, widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    email = forms.EmailField(label="Correo Electrónico", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    # Campos del Perfil (Manual)
    ruc = forms.CharField(label="RUC", max_length=13, widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance, 'perfil'):
            self.fields['ruc'].initial = self.instance.perfil.ruc
            self.fields['telefono'].initial = self.instance.perfil.telefono

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'perfil'):
                user.perfil.ruc = self.cleaned_data['ruc']
                user.perfil.telefono = self.cleaned_data['telefono']
                user.perfil.save()
            else:
                PerfilUsuario.objects.create(
                    user=user,
                    ruc=self.cleaned_data['ruc'],
                    telefono=self.cleaned_data['telefono']
                )
        return user

# --- 4. ALTA DE CONTRIBUYENTE (REGISTRO RÁPIDO) ---

class AltaContribuyenteForm(forms.ModelForm):
    # CAMPOS DE USUARIO SEPARADOS
    cedula = forms.CharField(label="CÉDULA", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CÉDULA'}))
    first_name = forms.CharField(label="NOMBRES", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    last_name = forms.CharField(label="APELLIDOS", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'}))
    ruc_propietario = forms.CharField(label="RUC", max_length=13, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUC (13 DÍGITOS)'}))

    latitud = forms.CharField(widget=forms.HiddenInput(), required=False)
    longitud = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Establecimiento
        fields = ['razon_social', 'nombre_comercial', 'tipo', 'parroquia', 'direccion']
        widgets = {
            'razon_social': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'parroquia': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'EJ: CALLE SUCRE Y BOLÍVAR'}),
        }

    def save(self, commit=True):
        cedula = self.cleaned_data['cedula']
        first_name = self.cleaned_data['first_name'].upper()
        last_name = self.cleaned_data['last_name'].upper()
        ruc = self.cleaned_data['ruc_propietario']
        
        # Gestión de Usuario
        user, created = User.objects.get_or_create(username=cedula)
        
        if created:
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(cedula) 
            user.save()
            PerfilUsuario.objects.create(user=user, ruc=ruc)
        else:
            # Actualizar datos si faltan
            if not user.first_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save()
            if not hasattr(user, 'perfil'):
                PerfilUsuario.objects.create(user=user, ruc=ruc)
        
        # Gestión de Establecimiento
        establecimiento = super().save(commit=False)
        establecimiento.propietario = user
        
        if commit:
            establecimiento.save()
        return establecimiento

# --- 5. REGISTRO DE EMAIL (ONBOARDING) ---

class RegistroEmailForm(forms.ModelForm):
    email = forms.EmailField(
        label="Correo Electrónico Personal", 
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-darker text-white border-secondary', 
            'placeholder': 'ejemplo@gmail.com'
        })
    )

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado por otro usuario.")
        return email

# --- 6. PERFIL DE USUARIO (AUTOGESTIÓN) ---

class MiPerfilForm(forms.ModelForm):
    # 1. CAMPOS BLOQUEADOS (Solo Lectura)
    first_name = forms.CharField(
        label="Nombres", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control-plaintext text-white opacity-75', 'readonly': True})
    )
    last_name = forms.CharField(
        label="Apellidos", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control-plaintext text-white opacity-75', 'readonly': True})
    )
    cedula_readonly = forms.CharField(
        label="Cédula / Usuario", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control-plaintext text-white fw-bold', 'readonly': True})
    )
    ruc_readonly = forms.CharField(
        label="RUC", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control-plaintext text-white font-monospace', 'readonly': True})
    )

    # 2. CAMPOS EDITABLES CON VALIDACIÓN
    email = forms.EmailField(
        label="Email de Contacto", 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    telefono = forms.CharField(
        label="Teléfono Celular", 
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'El teléfono debe tener 10 dígitos numéricos.')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'number'})
    )

    class Meta:
        model = User
        fields = ['email'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['cedula_readonly'].initial = self.instance.username
            
            if hasattr(self.instance, 'perfil'):
                self.fields['telefono'].initial = self.instance.perfil.telefono
                self.fields['ruc_readonly'].initial = self.instance.perfil.ruc
            else:
                self.fields['ruc_readonly'].initial = "N/A"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso por otro usuario.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'perfil'):
                user.perfil.telefono = self.cleaned_data['telefono']
                user.perfil.fecha_ultima_actualizacion = date.today()
                user.perfil.save()
            else:
                PerfilUsuario.objects.create(
                    user=user, 
                    telefono=self.cleaned_data['telefono'],
                    fecha_ultima_actualizacion=date.today()
                )
        return user
class TasaPagoForm(forms.ModelForm):
    class Meta:
        model = TasaPago
        fields = ['tipo', 'descripcion', 'valor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select bg-slate-50 border-slate-300 rounded-lg w-full'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tasa administrativa 2025'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control font-bold text-emerald-600', 'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar: Solo mostrar tipos que AÚN NO tienen tasa asignada (para evitar duplicados)
        # Si estamos editando (instance.pk), mostramos el actual.
        if not self.instance.pk:
            tipos_con_tasa = TasaPago.objects.values_list('tipo_id', flat=True)
            self.fields['tipo'].queryset = TipoEstablecimiento.objects.exclude(id__in=tipos_con_tasa)

class RequisitoLegalForm(forms.ModelForm):
    class Meta:
        model = RequisitoLegal
        fields = ['seccion', 'orden', 'titulo', 'contenido']
        widgets = {
            'seccion': forms.Select(attrs={'class': 'form-select bg-slate-50 border-slate-300 rounded-lg w-full font-bold text-slate-700'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control font-bold', 'placeholder': 'Ej: Extintor PQS'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Debe ser de 10 libras, recargado anualmente...'}),
        }