import copy
from unittest import mock

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from .demo import DEMO_CARDS, DEMO_TEXT
from .models import Flashcard, Source
from .services import GenerationError


class HomeFlowTests(TestCase):
    def setUp(self):
        self.url = reverse("home")

    def test_valid_demo_post_redirects_and_creates_three_cards(self):
        response = self.client.post(
            self.url,
            {"title": "Компьютерные сети", "text": DEMO_TEXT},
        )

        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(Flashcard.objects.count(), 3)

        source = Source.objects.get()
        self.assertEqual(source.generation_mode, "demo")
        self.assertRedirects(
            response,
            reverse("source_detail", kwargs={"pk": source.pk}),
        )

        positions = list(
            Flashcard.objects.order_by("position").values_list("position", flat=True)
        )
        self.assertEqual(positions, [1, 2, 3])

    @mock.patch("study.views.generate_cards")
    def test_short_text_does_not_reach_provider(self, mock_generate):
        response = self.client.post(
            self.url,
            {"title": "T", "text": "тым қысқа мәтін"},
        )

        self.assertEqual(response.status_code, 200)
        mock_generate.assert_not_called()
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Flashcard.objects.count(), 0)

    def test_one_bad_quote_rejects_all_cards(self):
        bad_cards = copy.deepcopy(DEMO_CARDS)
        bad_cards[1]["source_quote"] = "Бұл сөйлем мәтінде жоқ."

        with mock.patch("study.services.DEMO_CARDS", bad_cards):
            response = self.client.post(
                self.url,
                {"title": "T", "text": DEMO_TEXT},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Flashcard.objects.count(), 0)
        self.assertTrue(response.context["form"].non_field_errors())

    @mock.patch(
        "study.views.generate_cards",
        side_effect=GenerationError("provider failure"),
    )
    def test_provider_generation_error_keeps_bound_form(self, mock_generate):
        response = self.client.post(
            self.url,
            {"title": "T", "text": DEMO_TEXT},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["REQUEST_METHOD"], "POST")
        self.assertIn(
            "provider failure",
            response.context["form"].non_field_errors(),
        )
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Flashcard.objects.count(), 0)

    def test_database_error_rolls_back_source_and_first_card(self):
        def fake_bulk_create(cards_list, *args, **kwargs):
            first = cards_list[0]
            Flashcard.objects.create(
                source=first.source,
                position=first.position,
                question=first.question,
                answer=first.answer,
                source_quote=first.source_quote,
            )
            raise DatabaseError("simulated failure on second card")

        with mock.patch.object(
            Flashcard.objects,
            "bulk_create",
            side_effect=fake_bulk_create,
        ):
            response = self.client.post(
                self.url,
                {"title": "T", "text": DEMO_TEXT},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Flashcard.objects.count(), 0)

    @mock.patch("study.views.generate_cards")
    def test_detail_get_does_not_call_provider(self, mock_generate):
        source = Source.objects.create(
            title="X",
            text=DEMO_TEXT,
            generation_mode="demo",
        )
        Flashcard.objects.create(
            source=source,
            position=1,
            question="Q?",
            answer="A.",
            source_quote="A.",
        )

        url = reverse("source_detail", kwargs={"pk": source.pk})
        before_sources = Source.objects.count()
        before_cards = Flashcard.objects.count()

        r1 = self.client.get(url)
        r2 = self.client.get(url)

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        mock_generate.assert_not_called()
        self.assertEqual(Source.objects.count(), before_sources)
        self.assertEqual(Flashcard.objects.count(), before_cards)