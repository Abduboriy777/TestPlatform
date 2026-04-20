from django import forms
from accounts.models import User
from .models import ChatRoom


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class GroupCreateForm(BootstrapMixin, forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple,
        required=False,
    )

    class Meta:
        model = ChatRoom
        fields = ["name"]