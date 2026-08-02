from enum import Enum
from typing import List, Optional

class PieceType(Enum):
    X = "X"
    O = "O"

class Cell:
    def __init__(self):
        self._piece: Optional[PieceType] = None

    def is_empty(self) -> bool:
        return self._piece is None

    def set_piece(self, piece: PieceType) -> None:
        self._piece = piece

    def get_piece(self) -> Optional[PieceType]:
        return self._piece

class Player:
    def __init__(self, name: str, piece: PieceType):
        self._name: str = name
        self._piece: PieceType = piece

    @property
    def name(self) -> str:
        return self._name

    @property
    def piece(self) -> PieceType:
        return self._piece

class Board:
    def __init__(self, size: int = 3):
        self._size: int = size
        self._gird: List[List[Cell]] = [[Cell() for _ in range(size)] for _ in range(size)]

    @property
    def size(self) -> int:
        return self._size

    def is_valid_move(self, row: int, col: int) -> bool:
        return (0 <= row < self._size) and (0 <= col < self.size) and (self._grid[row][col].is_empty())

    def place_piece(self, row: int, col: int, piece: PieceType) -> bool:
        if not is_valid_move(row, col):
            return False

        self._grid[row][col].set_piece(piece)
        return True

    def get_cell_piece(self, row: int, col: int) -> Optional[PieceType]:
        return self._grid[row][col].get_piece()

    def display(self) -> None:
        for row in range(self._size):
            row_str = []
            for col in range(self._size):
                piece = self._grid[row][col].get_piece()
                row_str.append(piece.value if piece else " ")
                print(" | ". join(row_str))
                if row < self._size-1:
                    print("-"*(self._size*4-1))

class WinDetectionStrategy(ABC):
    @abstractmethod
    def check_win(self, board: Board, last_row: int, last_col: int, piece: PieceType) -> bool:
        pass

class StandardWinStrategy(WinDetectionStrategy):
    def check_win(self, board: Board, last_row: int, last_col: int, piece: PieceType) -> bool:
        size = board.size
        if all(board.get_cell_piece(last_row, c) == piece for c in range(size)):
            return True
        if all(board.get_cell_piece(r, last_col) == piece for r in range(size)):
            return True
        if last_row == last_col:
            if all(board.get_cell_piece(i, i) == piece for i in range(size)):
                return True
        if last_row + last_col == size-1:
            if all(board.get_cell_piece(i, last_col-i-1) == piece for i in range(size)):
                return True
        return False

class GameStatus(Enum):
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    WON = "WON"
    DRAW = "DRAW"

class GameEngine:
    def __init__(self, players: List[Player], board_size: int = 3, win_strategy: Optional[WinDetectionStrategy] = None):
        if len(players) < 2:
            raise ValueError("A minimum of 2 players is required.")

        self._players: List[Player] = players
        self._board: Board = Board(board_size)
        self._win_stragety: WinDetectionStrategy = win_strategy or StandardWinStrategy()

        self._status: GameStatus = GameStatus.READY
        self._current_player_idx: int = 0
        self._moves_played: int = 0
        self._max_moves: int = board_size*board_size
        self._winner: Optional[Player] = None

    @property
    def status(self) -> GameStatus:
        return self._status
    
    @property
    def winner(self) -> Optional[Player]:
        return self._winner

    def get_current_player(self) -> Player:
        return self._players[self._current_player_idx]

    def start_game(self) -> None:
        self._status = GameStatus.IN_PROGRESS
        print("Game Started!")
        self._board.display()

    def play_turn(self, row: int, col: int) -> bool:
        






















