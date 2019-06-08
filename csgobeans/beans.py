import enum

class Quality(enum.Enum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    MYTHIC = 4

class Color(enum.Enum):
    RED = 1
    ORANGE = 2
    YELLOW = 3
    GREEN = 4
    BLUE = 5
    PURPLE = 6
    BLACK = 7
    GREY = 8
    WHITE = 9

class Bean:
    def __init__(self, name, short_desc, color, quality):
        self.name = name
        self.short_desc = short_desc
        self.color = color
        self.quality = quality

    def __str__(self):
        return "Bean(\"{}\", \"{}\", {}, {})".format(
            self.name, self.short_desc, self.color, self.quality)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return all((
            self.name == other.name,
            self.short_desc == other.short_desc,
            self.color == other.color,
            self.quality == other.quality))
