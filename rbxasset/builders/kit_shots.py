"""Default preview shots, bpy-free."""


def default_shots(W, D, H):
    s = max(W, D, H)
    return [
        ("wide", (-s * 1.5, -s * 2.2, H * 0.6 + s * 0.4), (0.0, 0.0, H * 0.45), 40.0),
        ("close", (-s * 0.7, -s * 1.3, H * 0.7 + s * 0.1), (0.0, 0.0, H * 0.6), 50.0),
    ]
