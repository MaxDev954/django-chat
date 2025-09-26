from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import MyUser


@admin.register(MyUser)
class MyUserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_admin", "color", "avatar_preview")
    list_filter = ("is_active", "is_admin")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "color", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_admin")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "color", "avatar", "password1", "password2"),
        }),
    )

    filter_horizontal = ()

    def avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="30" height="30" style="border-radius:50%;" />'
        return "-"
    avatar_preview.allow_tags = True
    avatar_preview.short_description = "Avatar"
