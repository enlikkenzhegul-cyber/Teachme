import os

from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .demo import DEMO_TEXT, DEMO_TITLE
from .forms import SourceForm
from .models import Flashcard, Source
from .services import GenerationError, generate_cards


def home(request):
    saved_sources = Source.objects.all().order_by("-created_at")

    if request.method == "POST":
        form = SourceForm(request.POST)
        if form.is_valid():
            mode = os.environ.get("TEACHME_MODE", "demo").strip().lower()
            cards = None
            try:
                cards = generate_cards(form.cleaned_data["text"])
            except GenerationError as exc:
                form.add_error(None, str(exc))

            if cards is not None:
                try:
                    with transaction.atomic():
                        source = Source.objects.create(
                            title=form.cleaned_data["title"],
                            text=form.cleaned_data["text"],
                            generation_mode=mode,
                        )
                        Flashcard.objects.bulk_create(
                            [
                                Flashcard(
                                    source=source,
                                    position=index,
                                    question=card["question"],
                                    answer=card["answer"],
                                    source_quote=card["source_quote"],
                                )
                                for index, card in enumerate(cards, start=1)
                            ]
                        )
                except DatabaseError:
                    form.add_error(
                        None,
                        "Дерекқорға сақтау кезінде қате орын алды. Қайталап көріңіз.",
                    )
                else:
                    return redirect("source_detail", pk=source.pk)
    else:
        form = SourceForm(initial={"title": DEMO_TITLE, "text": DEMO_TEXT})

    return render(
        request,
        "study/home.html",
        {
            "form": form,
            "sources": saved_sources,
        },
    )


def source_detail(request, pk):
    source = get_object_or_404(Source, pk=pk)
    cards = source.cards.all()
    return render(
        request,
        "study/source_detail.html",
        {
            "source": source,
            "cards": cards,
        },
    )