class MazegenError(Exception):
    pass


class InvalidDimensionError(MazegenError):
    pass


class InvalidCoordinateError(MazegenError):
    pass


class ImpossibleMazeError(MazegenError):
    pass


class NoSolutionError(MazegenError):
    pass
