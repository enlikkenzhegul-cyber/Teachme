import os

from django.db import DatabaseError, transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .demo import DEMO_TEXT, DEMO_TITLE
from .forms import FlashcardForm, SourceForm
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

    all_cards = list(source.cards.all())
    total_count = len(all_cards)
    verified_count = sum(1 for card in all_cards if card.is_verified)
    pending_count = total_count - verified_count

    status = request.GET.get("status", "all")
    if status not in {"all", "pending", "verified"}:
        status = "all"

    if status == "pending":
        cards = [card for card in all_cards if not card.is_verified]
    elif status == "verified":
        cards = [card for card in all_cards if card.is_verified]
    else:
        cards = all_cards

    return render(
        request,
        "study/source_detail.html",
        {
            "source": source,
            "cards": cards,
            "status": status,
            "total_count": total_count,
            "verified_count": verified_count,
            "pending_count": pending_count,
        },
    )


def card_edit(request, pk):
    card = get_object_or_404(Flashcard, pk=pk)
    if request.method == "POST":
        form = FlashcardForm(request.POST, instance=card)
        if form.is_valid():
            card = form.save(commit=False)
            card.is_verified = False
            card.save()
            return redirect("source_detail", pk=card.source_id)
    else:
        form = FlashcardForm(instance=card)

    return render(
        request,
        "study/card_form.html",
        {
            "form": form,
            "card": card,
        },
    )


def card_delete(request, pk):
    card = get_object_or_404(Flashcard, pk=pk)
    source_id = card.source_id

    if request.method == "POST":
        card.delete()
        return redirect("source_detail", pk=source_id)

    return render(
        request,
        "study/card_confirm_delete.html",
        {
            "card": card,
        },
    )


@require_POST
def card_review(request, pk):
    card = get_object_or_404(Flashcard, pk=pk)
    action = request.POST.get("action")

    if action == "verify":
        card.is_verified = True
        card.save(update_fields=["is_verified"])
    elif action == "reset":
        card.is_verified = False
        card.save(update_fields=["is_verified"])
    else:
        return HttpResponseBadRequest("Белгісіз әрекет.")

    return redirect("source_detail", pk=card.source_id)