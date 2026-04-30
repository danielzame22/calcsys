# sudoku_engine.py — generador y solver puro Python
import random
from datetime import date


def _seeded_rng(seed):
    rnd = random.Random(seed)
    return rnd


def _seed_for_today():
    d = date.today()
    return d.year * 10000 + d.month * 100 + d.day


def _is_valid(board, pos, num):
    r, c = divmod(pos, 9)
    # row
    if num in board[r*9:(r+1)*9]:
        return False
    # col
    if num in [board[i*9+c] for i in range(9)]:
        return False
    # box
    br, bc = (r//3)*3, (c//3)*3
    for dr in range(3):
        for dc in range(3):
            if board[(br+dr)*9+(bc+dc)] == num:
                return False
    return True


def _solve(board):
    try:
        empty = board.index(0)
    except ValueError:
        return True
    for n in range(1, 10):
        if _is_valid(board, empty, n):
            board[empty] = n
            if _solve(board):
                return True
            board[empty] = 0
    return False


def _count_solutions(board, limit=2):
    count = [0]
    def bt(b):
        if count[0] >= limit:
            return
        try:
            empty = b.index(0)
        except ValueError:
            count[0] += 1
            return
        r, c = divmod(empty, 9)
        used = set()
        used.update(b[r*9:(r+1)*9])
        used.update(b[i*9+c] for i in range(9))
        br, bc = (r//3)*3, (c//3)*3
        for dr in range(3):
            for dc in range(3):
                used.add(b[(br+dr)*9+(bc+dc)])
        for n in range(1, 10):
            if n not in used:
                b[empty] = n
                bt(b)
                b[empty] = 0
    bt(list(board))
    return count[0]


def generate_daily_puzzle():
    """Returns (puzzle, solution) as flat lists of 81 ints."""
    rnd = _seeded_rng(_seed_for_today())

    board = [0] * 81
    # Fill 3 diagonal 3x3 boxes
    for box in range(3):
        nums = list(range(1, 10))
        rnd.shuffle(nums)
        k = 0
        for r in range(3):
            for c in range(3):
                board[(box*3+r)*9+(box*3+c)] = nums[k]
                k += 1

    _solve(board)
    solution = list(board)

    # Remove cells (target ~48 removed for medium difficulty)
    indices = list(range(81))
    rnd.shuffle(indices)
    puzzle = list(solution)
    removed = 0
    for idx in indices:
        if removed >= 46:
            break
        val = puzzle[idx]
        puzzle[idx] = 0
        if _count_solutions(puzzle) == 1:
            removed += 1
        else:
            puzzle[idx] = val

    return puzzle, solution


def solve_board(board):
    """Returns solved board or None."""
    b = list(board)
    if _solve(b):
        return b
    return None
