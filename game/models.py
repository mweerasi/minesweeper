from django.db import models


# Models for a minesweeper board

class Board(models.Model):
    """
    Represents a Minesweeper game board.
    """
    # Board dimensions are always square
    # For now, we'll keep it to 3 levels, 9x9 (10 Bombs), 16x16 (40 Bombs), and 24x24 (99 Bombs)
    class BoardLevel(models.IntegerChoices):
        NINE = 9, 'Nine'
        SIXTEEN = 16, 'Sixteen'
        TWENTY_FOUR = 24, 'Twenty Four'
        CUSTOM = 0, 'Custom'

    size = models.IntegerField(default=9)
    level = models.IntegerField(choices=BoardLevel.choices, default=BoardLevel.NINE)
    is_completed = models.BooleanField(default=False)
    success = models.BooleanField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bomb_count = models.IntegerField(default=0)

    def complete(self, outcome: bool) -> None:
        """
        Mark the board as completed and set the outcome.

        Args:
            outcome (bool): True if the game was won, False otherwise.
        """
        self.is_completed = True
        self.success = outcome
        self.save()

    def save(self, *args, **kwargs) -> None:
        """
        Save the board instance, ensuring the size is set for custom levels.
        """
        # Check that if the level is custom, the size is set
        if self.level == self.BoardLevel.CUSTOM and self.size is None:
            raise ValueError("Size must be set for custom level")
        elif self.level != self.BoardLevel.CUSTOM:
            self.size = self.level
        super().save(*args, **kwargs)


class Cell(models.Model):
    """
    Represents a cell in the Minesweeper game board.
    """
    class CellState(models.IntegerChoices):
        # States for the cell, -1 is a bomb and >=0 is the number of adjacent bombs
        BOMB = -1, 'Bomb'
        ZERO = 0, 'Zero'
        ONE = 1, 'One'
        TWO = 2, 'Two'
        THREE = 3, 'Three'
        FOUR = 4, 'Four'
        FIVE = 5, 'Five'
        SIX = 6, 'Six'
        SEVEN = 7, 'Seven'
        EIGHT = 8, 'Eight'

    board = models.ForeignKey(Board, related_name='cells', on_delete=models.CASCADE)
    x = models.IntegerField()
    y = models.IntegerField()
    state = models.IntegerField(choices=CellState.choices, null=True, default=None)
    # Revealed means the cell has been clicked by the user
    is_revealed = models.BooleanField(default=False)
    # Flagged means the user has flagged the cell
    is_flagged = models.BooleanField(default=False)

    def get_state(self) -> int:
        """
        Get the state of the cell. If the state is not set, calculate it based on adjacent bombs.

        Returns:
            int: The state of the cell.
        """
        # Return the state if it's already set
        if self.state is not None:
            return self.state

        if self.state == self.CellState.BOMB:
            return self.state

        # Calculate the state of the cell based on the number of adjacent bombs
        # Get all adjacent cells
        adjacent_cells = Cell.objects.filter(
            board=self.board,
            x__in=[self.x-1, self.x, self.x+1],
            y__in=[self.y-1, self.y, self.y+1]
        ).exclude(x=self.x, y=self.y)

        # Count the number of adjacent bombs
        bomb_count = adjacent_cells.filter(state=self.CellState.BOMB).count()

        # Set the state to the number of adjacent bombs
        self.state = bomb_count
        self.save(update_fields=['state'])

        return self.state