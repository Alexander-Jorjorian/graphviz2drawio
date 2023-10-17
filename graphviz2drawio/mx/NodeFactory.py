from graphviz2drawio.models import SVG
from graphviz2drawio.models.Rect import Rect
from .Node import Node
from .Text import Text
from PIL import ImageFont

class NodeFactory:
    def __init__(self, coords):
        super(NodeFactory, self).__init__()
        self.coords = coords

    def rect_from_svg_points(self, svg):
        points = svg.split(" ")
        points = [self.coords.translate(*p.split(",")) for p in points]
        min_x, min_y = points[0]
        width = 0
        height = 0
        for p in points:
            if p[0] < min_x:
                min_x = p[0]
            if p[1] < min_y:
                min_y = p[1]
        for p in points:
            test_width = p[0] - min_x
            test_height = p[1] - min_y
            if test_width > width:
                width = test_width
            if test_height > height:
                height = test_height
        return Rect(x=min_x, y=min_y, width=width, height=height)

    @staticmethod
    def rect_from_image(attrib):
        filtered = {
            k: float(v.strip("px"))
            for k, v in attrib.items()
            if k in ["x", "y", "width", "height"]
        }

        return Rect(**filtered)

    def rect_from_ellipse_svg(self, attrib):
        cx = float(attrib["cx"])
        cy = float(attrib["cy"])
        rx = float(attrib["rx"])
        ry = float(attrib["ry"])
        x, y = self.coords.translate(cx, cy)
        return Rect(x=x - rx, y=y - ry, width=rx * 2, height=ry * 2)

    def rect_from_text(self, text):
        x = float(text.attrib["x"])
        y = float(text.attrib["y"])
        text_content = text.text
        font_size = int(float(text.attrib.get("font-size", 12)))
        font = ImageFont.truetype("arial.ttf", int(font_size))
        width, height = font.getsize(text_content)
        x, y = self.coords.translate(x, y)
        return Rect(x=x, y=y, width=width, height=height)

    def from_svg(self, g):
        texts = []
        current_text = None
        for t in g:
            if SVG.is_tag(t, "text"):
                if current_text is None:
                    current_text = Text.from_svg(t)
                else:
                    current_text.text += f"<br/>{t.text}"
            elif current_text is not None:
                texts.append(current_text)
                current_text = None
        print(SVG.get_title(g))
        for t in g.iter():
            print(t.tag)
        if current_text is not None:
            texts.append(current_text)
        if SVG.has(g, "polygon"):
            rect = self.rect_from_svg_points(SVG.get_first(g, "polygon").attrib["points"])
        elif SVG.has(g, "image"):
            rect = self.rect_from_image(SVG.get_first(g, "image").attrib)
        elif SVG.has(g, "ellipse"):
            rect = self.rect_from_ellipse_svg(SVG.get_first(g, "ellipse").attrib)
        else:
            if SVG.has(g, "text"):
                print(SVG.get_first(g, "text").attrib)
                rect = self.rect_from_text(SVG.get_first(g, "text"))
            else:
                raise RuntimeError("Unknown SVG tag in node")

        stroke = None
        if SVG.has(g, "polygon"):
            polygon = SVG.get_first(g, "polygon")
            if "stroke" in polygon.attrib:
                stroke = polygon.attrib["stroke"]

        return Node(
            sid=g.attrib["id"],
            gid=SVG.get_title(g),
            rect=rect,
            texts=texts,
            fill=g.attrib.get("fill", None),
            stroke=stroke,
        )
