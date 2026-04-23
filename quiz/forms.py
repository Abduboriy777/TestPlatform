from django import forms
from .models import Subject, Quiz, Question, Feedback


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            elif isinstance(widget, forms.Textarea):
                widget.attrs['class'] = 'form-control'
                widget.attrs['rows'] = 4
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs['class'] = 'form-control'
            else:
                widget.attrs['class'] = 'form-control'


class SubjectForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']


class QuizForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'subject', 'title', 'description', 'duration_minutes', 'pass_percentage',
            'status', 'difficulty', 'randomize_questions', 'randomize_choices'
        ]


class QuestionCreateForm(BootstrapMixin, forms.Form):
    text = forms.CharField(max_length=500)
    image = forms.ImageField(required=False)
    explanation = forms.CharField(required=False, widget=forms.Textarea)
    order = forms.IntegerField(min_value=1, initial=1)
    choice_1 = forms.CharField(max_length=255)
    choice_2 = forms.CharField(max_length=255)
    choice_3 = forms.CharField(max_length=255)
    choice_4 = forms.CharField(max_length=255)
    correct_choice = forms.ChoiceField(
        choices=[('1', '1-variant'), ('2', '2-variant'), ('3', '3-variant'), ('4', '4-variant')],
        widget=forms.Select
    )


class FeedbackForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['text']