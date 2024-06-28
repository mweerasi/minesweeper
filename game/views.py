from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Board, Cell
from .serializers import BoardSerializer, CellSerializer
from .utils.game_logic import create_board, reveal_adjacent_cells, check_successful_completion

class BoardViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing board instances.
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    @action(detail=False, methods=['post'])
    def create_board(self, request):
        """
        Create a new board based on the provided difficulty level.

        Args:
            request: The HTTP request containing the difficulty level.

        Returns:
            Response: The created board serialized data.
        """
        level = request.data.get('level')
        board = create_board(level)
        serializer = self.get_serializer(board)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_board(self, request, pk=None):
        """
        Retrieve a specific board by its primary key.

        Args:
            request: The HTTP request.
            pk: The primary key of the board to retrieve.

        Returns:
            Response: The serialized data of the requested board.
        """
        board = self.get_object()
        serializer = self.get_serializer(board)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_status(self, request, pk=None):
        """
        Retrieve the status of a specific board, including its cells.

        Args:
            request: The HTTP request.
            pk: The primary key of the board to retrieve the status for.

        Returns:
            Response: The serialized data of the board and its cells.
        """
        board = self.get_object()
        cells = board.cells.all()
        cell_serializer = CellSerializer(cells, many=True)
        return Response({
            'board': self.get_serializer(board).data,
            'cells': cell_serializer.data
        })

class CellViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing cell instances.
    """
    queryset = Cell.objects.all()
    serializer_class = CellSerializer

    @action(detail=True, methods=['get'])
    def get_cell(self, request, pk=None):
        """
        Retrieve a specific cell by its primary key.

        Args:
            request: The HTTP request.
            pk: The primary key of the cell to retrieve.

        Returns:
            Response: The serialized data of the requested cell.
        """
        cell = self.get_object()
        serializer = self.get_serializer(cell)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def flag_cell(self, request, pk=None):
        """
        Flag or unflag a specific cell.

        Args:
            request: The HTTP request.
            pk: The primary key of the cell to flag/unflag.

        Returns:
            Response: The serialized data of the updated cell and its board.
        """
        cell = self.get_object()

        # Check if the cell is already revealed
        if cell.is_revealed:
            return Response({'detail': 'Cannot flag a revealed cell'}, status=status.HTTP_400_BAD_REQUEST)

        cell.is_flagged = not cell.is_flagged
        cell.save()

        # Check if the game is successfully completed
        check_successful_completion(cell.board)

        # Return the updated cell
        cells_serializer = CellSerializer([cell], many=True)
        return Response({
            'board': BoardSerializer(cell.board).data,
            'updated_cells': cells_serializer.data
        })

    @action(detail=True, methods=['post'])
    def reveal_cell(self, request, pk=None):
        """
        Reveal a specific cell. If the cell is a bomb, mark the game as lost.
        If the cell is a zero, reveal adjacent cells.

        Args:
            request: The HTTP request.
            pk: The primary key of the cell to reveal.

        Returns:
            Response: The serialized data of the updated cells and the board.
        """
        cell = self.get_object()

        # Check if the cell is flagged
        if cell.is_flagged:
            return Response({'detail': 'Cannot reveal a flagged cell'}, status=status.HTTP_400_BAD_REQUEST)

        if cell.is_revealed:
            return Response({'detail': 'Cell is already revealed'}, status=status.HTTP_400_BAD_REQUEST)

        updated_cells = []
        if cell.state == Cell.CellState.BOMB:
            cell.board.complete(False)
            cell.is_revealed = True
            cell.save()
            updated_cells = [cell]
        elif cell.state == Cell.CellState.ZERO:
            updated_cells = reveal_adjacent_cells(cell)
        else:
            cell.is_revealed = True
            cell.save()
            updated_cells = [cell]

        check_successful_completion(cell.board)

        cells_serializer = CellSerializer(updated_cells, many=True)
        return Response({
            'board': BoardSerializer(cell.board).data,
            'updated_cells': cells_serializer.data
        })