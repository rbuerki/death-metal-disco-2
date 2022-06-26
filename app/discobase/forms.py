from django import forms

from discobase.choices import format_choices, genre_choices, rating_choices


class DateForm(forms.Form):
    """Set min and max date for chart display."""

    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class SearchForm(forms.Form):
    """Search records over multiple fields."""

    artist = forms.CharField(required=False)
    title = forms.CharField(required=False)
    genre = forms.MultipleChoiceField(
        choices=genre_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    record_format = forms.MultipleChoiceField(
        choices=format_choices, required=False, widget=forms.RadioSelect()
    )
    min_purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    max_purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    rating = forms.MultipleChoiceField(choices=rating_choices, required=False)
