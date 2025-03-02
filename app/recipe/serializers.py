"""
Serializers for recipe APIs
"""
from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingridient,
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngridientSerializer(serializers.ModelSerializer):
    """Serializer for ingridient class model"""

    class Meta:
        model = Ingridient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""
    tags = TagSerializer(many=True, required=False)
    ingridients = IngridientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link', 'tags',
            'ingridients',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handling getting or creating tags as needed"""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingridients(self, ingridients, recipe):
        """Handle getting or creating ingridietns as needed"""
        auth_user = self.context['request'].user
        for ingridient in ingridients:
            ingridient_obj, create = Ingridient.objects.get_or_create(
                user=auth_user,
                **ingridient,
            )
            recipe.ingridients.add(ingridient_obj)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        ingridients = validated_data.pop('ingridients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingridients(ingridients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update recipe"""
        tags = validated_data.pop('tags', None)
        ingridients = validated_data.pop('ingridients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingridients is not None:
            instance.ingridients.clear()
            self._get_or_create_ingridients(ingridients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for reipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to reciper"""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
