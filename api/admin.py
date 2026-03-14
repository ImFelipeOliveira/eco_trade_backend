from django.contrib import admin
from .models import User, ComercioProfile, ProdutorProfile, Lote, Scheduling

admin.site.register(User)
admin.site.register(ComercioProfile)
admin.site.register(ProdutorProfile)
admin.site.register(Lote)
admin.site.register(Scheduling) 