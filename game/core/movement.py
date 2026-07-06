def clamp_pos(row, col, rows, cols):
    row = max(0, min(rows - 1, row))
    col = max(0, min(cols - 1, col))
    return row, col


def same_line(pos_a, pos_b):
    row_a, col_a = pos_a
    row_b, col_b = pos_b
    return row_a == row_b or col_a == col_b
