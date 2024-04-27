class BoundingBox:
    def __init__(self, bbox, text, prob=0):
        self.bbox = bbox
        (tl, tr, br, bl) = bbox
        self.tl = (int(tl[0]), int(tl[1]))
        self.tr = (int(tr[0]), int(tr[1]))
        self.br = (int(br[0]), int(br[1]))
        self.bl = (int(bl[0]), int(bl[1]))
        self.width = abs(br[0] - tl[0])
        self.height = abs(br[1] - tl[1])
        self.text = text
        self.prob = prob
        self.x_top = tl[0]
        self.y_top = tl[1]

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

    def __lt__(self, other):
        # If other's top-left y is within 0.5 * self height, compare by x coordinate
        if self.y_top - 0.5 * self.height < other.y_top < self.y_top + 0.5 * self.height:
            return self.x_top < other.x_top
        # Otherwise, compare by y coordinate
        return self.y_top < other.y_top

    def __str__(self):
        return f"BoundingBox(tl={self.tl}, br={self.br}, width={self.width}, height={self.height}, text='{self.text}', confidence={self.confidence})"

    def __repr__(self):
        return f"BoundingBox({self.tl}, {self.br}, '{self.text}', {self.confidence})"
