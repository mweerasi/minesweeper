# Logic for the minesweeper game
from random import sample
from game.models import Board, Cell


def get_mine_count(level: int) -> int:
    """
    Get the number of mines based on the difficulty level.

    Args:
        level (int): The difficulty level of the board.

    Returns:
        int: The number of mines for the given difficulty level.
    """
    if level == 9:
        return 10
    elif level == 16:
        return 40
    elif level == 24:
        return 99

    return 100


def update_adjacent_counts(board: Board) -> None:
    """
    Update the state of each cell based on the number of adjacent mines.

    Args:
        board (Board): The board object containing all cells.
    """
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    cells = list(board.cells.all())
    bomb_positions = {(cell.x, cell.y) for cell in cells if cell.state == Cell.CellState.BOMB}

    for cell in cells:
        if cell.state == Cell.CellState.BOMB:
            continue

        adjacent_mines = sum(
            (cell.x + dx, cell.y + dy) in bomb_positions
            for dx, dy in directions
        )

        cell.state = adjacent_mines

    # Bulk update the state of all non-bomb cells
    Cell.objects.bulk_update([cell for cell in cells if cell.state != Cell.CellState.BOMB], ['state'])


def create_board(level: int) -> Board:
    """
    Create a new board based on the difficulty level.

    Args:
        level (int): The difficulty level of the board.

    Returns:
        Board: The created board object.
    """
    board = Board.objects.create(level=level, bomb_count=get_mine_count(level))
    size = board.size

    cells = [Cell(board=board, x=x, y=y) for x in range(size) for y in range(size)]
    Cell.objects.bulk_create(cells)

    mines = sample(cells, board.bomb_count)
    for mine in mines:
        mine.state = Cell.CellState.BOMB

    # Bulk update the state of the mines
    Cell.objects.bulk_update(mines, ['state'])

    update_adjacent_counts(board)

    return board


def check_successful_completion(board: Board) -> None:
    """
    Check if the game is successfully completed.

    Args:
        board (Board): The board object to check for completion.
    """
    flagged_bombs_count = board.cells.filter(state=Cell.CellState.BOMB, is_flagged=True).count()
    revealed_non_bombs_count = board.cells.filter(state__gte=0, is_revealed=True).count()
    total_non_bombs_count = board.cells.filter(state__gte=0).count()

    if flagged_bombs_count == board.bomb_count and revealed_non_bombs_count == total_non_bombs_count:
        board.complete(True)


def reveal_adjacent_cells(cell: Cell) -> list[Cell]:
    """
    Reveal the adjacent cells if the current cell is a zero.

    Args:
        cell (Cell): The cell to start revealing from.

    Returns:
        List[Cell]: The list of cells that were revealed.
    """
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    cells_to_reveal = [cell]
    cells_to_update = []
    seen_cells = set()

    while cells_to_reveal:
        current_cell = cells_to_reveal.pop()
        if current_cell.is_revealed:
            continue

        current_cell.is_revealed = True
        cells_to_update.append(current_cell)
        seen_cells.add((current_cell.x, current_cell.y))

        if current_cell.state == Cell.CellState.ZERO:
            for dx, dy in directions:
                nx, ny = current_cell.x + dx, current_cell.y + dy
                if 0 <= nx < current_cell.board.size and 0 <= ny < current_cell.board.size:
                    adjacent_cell = Cell.objects.filter(board=current_cell.board, x=nx, y=ny).first()
                    if adjacent_cell and not adjacent_cell.is_revealed and (nx, ny) not in seen_cells:
                        cells_to_reveal.append(adjacent_cell)
                        seen_cells.add((nx, ny))

    # Batch update all revealed cells
    Cell.objects.bulk_update(cells_to_update, ['is_revealed'])
    return cells_to_update