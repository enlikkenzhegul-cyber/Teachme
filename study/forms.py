from django import forms

from .models import Flashcard


class SourceForm(forms.Form):
    title = forms.CharField(max_length=120)
    text = forms.CharField(
        min_length=80,
        max_length=12000,
        widget=forms.Textarea,
        strip=True,
    )

    def clean_text(self):
        text = self.cleaned_data["text"]
        return text.replace("\r\n", "\n").replace("\r", "\n")


class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ["question", "answer", "source_quote"]

    def clean_source_quote(self):
        quote = self.cleaned_data["source_quote"]
        quote = quote.replace("\r\n", "\n").replace("\r", "\n")
        source_text = self.instance.source.text
        if quote not in source_text:
            raise forms.ValidationError(
                "Дәйексөз бастапқы мәтінде дәл осылай кездеспейді. "
                "Мәтіннен нақты үзінді көшіріп қойыңыз."
            )
        return quote