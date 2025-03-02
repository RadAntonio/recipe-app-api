"""Test for ingriddients API"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingridient,
    Recipe,
)

from recipe.serializers import IngridientSerializer


INGRIDIENTS_URL = reverse('recipe:ingridient-list')


def detail_url(ingridient_id):
    """Create and return an ingridient detail url"""
    return reverse('recipe:ingridient-detail', args=[ingridient_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngridientsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingridients"""
        res = self.client.get(INGRIDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngridientsApiTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingridients(self):
        """Test retrieveing list of ingridients"""
        Ingridient.objects.create(user=self.user, name='Kale')
        Ingridient.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(INGRIDIENTS_URL)

        ingridients = Ingridient.objects.all().order_by('-name')
        serializer = IngridientSerializer(ingridients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingridients_limited_to_user(self):
        """Test list of ingridients is limited to authenticated user"""
        user2 = create_user(email='user2@example.com', password='testpass123')
        Ingridient.objects.create(user=user2, name='Salt')
        ingridient = Ingridient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGRIDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingridient.name)
        self.assertEqual(res.data[0]['id'], ingridient.id)

    def test_update_ingridient(self):
        """Test updating an ingridient"""
        ingridient = Ingridient.objects.create(user=self.user, name='Cilantro')

        payload = {'name': 'Coriander'}
        url = detail_url(ingridient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingridient.refresh_from_db()
        self.assertEqual(ingridient.name, payload['name'])

    def test_delete_ingridient(self):
        """Test deleting an ingridient"""
        ingridient = Ingridient.objects.create(user=self.user, name='Lettuce')

        url = detail_url(ingridient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingridients = Ingridient.objects.filter(user=self.user)
        self.assertFalse(ingridients.exists())

    def test_ingridients_assigned_to_recipes(self):
        """Test filtering ingridients by those assigned to recipes"""
        in1 = Ingridient.objects.create(user=self.user, name='Apples')
        in2 = Ingridient.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Apple crumble',
            time_minutes=5,
            price=Decimal('4.50'),
        )
        recipe.ingridients.add(in1)

        res = self.client.get(INGRIDIENTS_URL, {'assigned_only': 1})

        s1 = IngridientSerializer(in1)
        s2 = IngridientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingridients_unique(self):
        """Test filtered ingridients retrurns a unique list"""
        ing = Ingridient.objects.create(user=self.user, name='Eggs')
        Ingridient.objects.create(user=self.user, name='Lentils')
        recipe1 = Recipe.objects.create(
            title='Scrambled eggs',
            time_minutes=5,
            price=Decimal('3.00'),
            user=self.user,
        )
        recipe1.ingridients.add(ing)
        recipe2 = Recipe.objects.create(
            title='Egg salad',
            time_minutes=10,
            price=Decimal('4.00'),
            user=self.user,
        )
        recipe2.ingridients.add(ing)

        res = self.client.get(INGRIDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
