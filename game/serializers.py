# serializers.py
from rest_framework import serializers
from .models import Board, Cell

class CellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell
        fields = ['id', 'x', 'y', 'state', 'is_revealed', 'is_flagged']

class BoardSerializer(serializers.ModelSerializer):
    cells = CellSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'size', 'level', 'is_completed','success', 'created_at', 'updated_at', 'bomb_count', 'cells']
