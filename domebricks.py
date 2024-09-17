# encoding=utf-8
import argparse
import math
from uuid import uuid4

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4


class Point():
    """Point on the x/y plain."""
    def __init__(self, title, x, y):
        self.title = title
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.title}({self.x}, {self.y})'

    def __repr__(self):
        return f'{self.title}({self.x}, {self.y})'

    def as_tuple(self):
        return (self.x, self.y)

    def as_csv(self, fill='green'):
        return f'''
            <text fill="{fill}" x="{self.x - 20}" y="{self.y - 10}">
                {self.title}
            </text>
            <circle cx="{self.x}"
                    cy="{self.y}"
                    r="3"
                    fill="black"
                    fill-opacity="0.8"/>'''


class Path():
    """Path from one point to another."""
    def __init__(self, p1, p2, distance=None):
        self.path_id = f'path-{uuid4().hex}'
        self.p1 = p1
        self.p2 = p2
        if distance is None:
            distance = get_distance(p1, p2)
        self.distance = distance

    def as_csv(self, y_offset=0, stroke='black', inner_text=False,
               rotate=0, dasharray=False, opacity=None,
               outside_path=False, move_bottom=False, move_left=False,
               x_offset=0, distance_fill=None):

        if not distance_fill:
            distance_fill = stroke

        dy = 16

        if y_offset:
            dy += y_offset
        if inner_text:
            dy = dy + 10
        else:
            dy = dy * -1

        if rotate:
            transform = f'transform="rotate({rotate})"'
        else:
            transform = ''
        if dasharray:
            stroke_dasharray = 'stroke-dasharray="6"'
        else:
            stroke_dasharray = ''

        if opacity is not None:
            stroke_opacity = f'stroke-opacity="{opacity}"'
        else:
            stroke_opacity = ''

        ret = []
        path = f'''
            <path id="{self.path_id}"
                  {stroke_dasharray}
                  {stroke_opacity}
                  stroke-width="2"
                  stroke="{stroke}"
                  d="M{self.p1.x},{self.p1.y} L{self.p2.x},{self.p2.y}"
                  fill="none" />
        '''
        ret.append(path)

        if outside_path:
            if move_bottom:
                text_y = self.p1.y + 20
            else:
                text_y = self.p1.y - 10
            if move_left:
                text_x = self.p1.x + 10
            else:
                text_x = self.p1.x - 10
            if x_offset:
                text_x += x_offset
            if y_offset:
                text_y += y_offset
            text = f'''
                <text
                    dx="{text_x}"
                    dy="{text_y}"
                    fill="{distance_fill}"
                    style="transform-box: fill-box; transform-origin: center;"
                    {transform}>
                        {self.distance}
                </text>
                '''
        else:
            text = f'''
                <text
                    dx="0"
                    dy="{dy}"
                    style="transform-box: fill-box; transform-origin: center;"
                    {transform}>

                    <textPath href="#{self.path_id}"
                              font-family="Verdana"
                              font-size="14"
                              fill="{distance_fill}">
                        {self.distance}
                    </textPath>
                </text>
            '''

        ret.append(text)
        return ''.join(ret)


class Row():

    """Row of bricks of the dome."""

    def __init__(
            self, surface_circle_center_point, inner_radius, bottom_radian,
            bottom_radian_point, number, brick_height=65,
            outer_height=208,
            bottom_seam=6.0, vertical=False, brick_width=250,
            brick_depth=120):
        """
        Args:
            bottom_radian: previous brick radian.
            bottom_radian_point: previous brick radian point.
        """
        self.vertical = vertical
        self.brick_height = brick_height
        self.brick_depth = brick_depth
        self.number = number
        self.bottom_seam = bottom_seam
        self.surface_circle_center_point = surface_circle_center_point

        self.inner_radius = inner_radius
        if vertical:
            self.outer_radius = inner_radius + brick_depth
        else:
            self.outer_radius = inner_radius + brick_width / 2.0
        self.outer_height = outer_height

        self.bottom_radian, self.bottom_radian_point = move_along_radius(
            radian_point=bottom_radian_point,
            circle_center_point=surface_circle_center_point,
            distance=self.bottom_seam, radius=self.outer_radius)

        self.bottom_outer_point = self._get_bottom_outer_point()
        self.top_radian, self.top_outer_point = self._get_top_outer_point()

        self.bottom_inner_point = self._get_bottom_inner_point()
        self.top_inner_point = self._get_top_inner_point()

    def _get_top_outer_point(self):

        if self.vertical:
            # FIXME: Use move_along_radius instead of loop.
            # radian, new_point = move_along_radius(
            #     radian_point=self.bottom_radian_point,
            #     circle_center_point=self.surface_circle_center_point,
            #     distance=self.brick_height, radius=self.outer_radius)
            # return radian, new_point
            step = 0.0001
            radian = self.bottom_radian
            new_x = self.bottom_outer_point.x
            safety_counter = 10000
            while True:
                safety_counter -= 1
                if safety_counter <= 0:
                    raise RuntimeError(
                        'Could not find vertical brick radian and point.')
                radian -= step
                new_y = self.surface_circle_center_point.y \
                    - self.outer_radius\
                    * math.sin(radian)
                new_point = Point(f'#{self.number}-TOP', new_x, new_y)
                if get_distance(new_point, self.bottom_outer_point) \
                        >= self.outer_height:
                    return radian, new_point
        else:
            radian, new_point = move_along_radius(
                radian_point=self.bottom_radian_point,
                circle_center_point=self.surface_circle_center_point,
                distance=self.outer_height, radius=self.outer_radius)
            return radian, new_point
        raise RuntimeError('Could not move to top outer point.')

    def _get_bottom_inner_point(self):
        if self.vertical:
            new_y = self.bottom_outer_point.y
        else:
            new_y = self.surface_circle_center_point.y \
                - self.inner_radius \
                * math.sin(self.bottom_radian)
        new_x = self.surface_circle_center_point.x \
            + self.inner_radius \
            * math.cos(self.bottom_radian)
        new_point = Point('BIP', new_x, new_y)
        return new_point

    def _get_bottom_outer_point(self):
        if self.vertical:
            radian_point_distance = get_distance(
                self.bottom_radian_point,
                self.surface_circle_center_point)
            return Point(
                '?',
                self.bottom_radian_point.x + radian_point_distance - self.outer_radius,  # noqa: E501
                self.bottom_radian_point.y + self.brick_height)
        else:
            return self.bottom_radian_point

    def _get_top_inner_point(self):
        if self.vertical:
            new_x = self.bottom_inner_point.x
        else:
            new_x = self.surface_circle_center_point.x \
                + self.inner_radius \
                * math.cos(self.top_radian)
        new_y = self.surface_circle_center_point.y \
            - self.inner_radius \
            * math.sin(self.top_radian)
        new_point = Point('TIP', new_x, new_y)
        return new_point

    def __repr__(self):
        return '#{}'.format(self.number)

    def get_brick_elems(self):
        elems = []
        elems.append(
            Path(self.bottom_outer_point, self.top_outer_point)
            .as_csv(stroke='orange'))
        elems.append(
            Path(self.top_outer_point, self.top_inner_point)
            .as_csv(stroke='orange', inner_text=True))
        elems.append(
            Path(self.top_inner_point, self.bottom_inner_point)
            .as_csv(stroke='orange', inner_text=True, rotate=180))
        elems.append(
            Path(self.bottom_inner_point, self.bottom_outer_point, distance='')
            .as_csv(stroke='orange', inner_text=True))
        elems.append(self.top_outer_point.as_csv())
        return elems


def render_row_brick_template(
        cnv, bricks_amount, a_point, b_point, c_point, d_point,
        e_point, f_point, g_point, h_point,
        brick_height=65, brick_width=250,
        row_number=None, inner_outer_diff=None,
        vertical_seam=4):
    assert inner_outer_diff is not None
    start_y = 285
    start_x = 20
    point_a = (start_x*mm, start_y*mm)
    cnv.drawString(point_a[0] + 5, point_a[1] - 15, 'A')

    point_b = (point_a[0] + get_distance(e_point, f_point)*mm, start_y*mm)
    cnv.drawString(point_b[0] - 15, point_b[1] - 15, 'B')
    cnv.setDash(6, 3)
    cnv.line(point_a[0], point_a[1], point_b[0], point_b[1])
    cnv.drawString(
        point_a[0] + 40, point_a[1] - 20,
        'AB({})'.format(float_format((point_b[0] - point_a[0]) / mm)))

    length_diff1 = (b_point.x - a_point.x) - (f_point.x - e_point.x)
    point_c = (point_a[0] - length_diff1*mm / 2, (start_y-brick_height)*mm)
    cnv.drawString(point_c[0] + 5, point_c[1] - 15, 'C')
    cnv.drawString(point_c[0] + 5, point_c[1] + 15, 'C')

    cnv.drawString(
        point_a[0] + 20, point_a[1] - 80,
        'AC({})'.format(float_format(get_distance1(point_c, point_a) / mm)))

    point_d = ((point_b[0] + length_diff1*mm / 2), (start_y-brick_height)*mm)
    cnv.drawString(point_d[0] - 15, point_d[1] - 15, 'D')
    cnv.drawString(point_d[0] - 15, point_d[1] + 15, 'D')
    cnv.setDash()
    cnv.line(point_c[0], point_c[1], point_d[0], point_d[1])
    cnv.drawString(
        point_c[0] + 40, point_c[1] + 10,
        'CD({})'.format(float_format((point_d[0] - point_c[0]) / mm)))

    # Render row details
    cnv.drawString(
        point_c[0] + 20, point_c[1] - 35,
        f'Row #{row_number}.')
    cnv.drawString(
        point_c[0] + 20, point_c[1] - 50,
        f'bricks_amount: {bricks_amount}')
    cnv.drawString(
        point_c[0] + 20, point_c[1] - 65,
        f'vertical seam: {vertical_seam}')

    length_diff2 = (b_point.x - a_point.x) - (c_point.x - d_point.x)
    point_e = (
        point_c[0] + length_diff2*mm / 2,
        (start_y-brick_height-brick_width/2)*mm)

    point6 = (
        point_d[0] - length_diff2*mm / 2,
        (start_y-brick_height-brick_width/2)*mm)
    cnv.setDash()
    cnv.line(point_e[0], point_e[1], point6[0], point6[1])
    cnv.drawString(
        point_e[0] + 40, point_e[1] + 10,
        'EF({})'.format(float_format((point6[0] - point_e[0]) / mm)))

    cnv.drawString(
        point_c[0] + 20, point_c[1] - get_distance1(point_c, point_e) / 2.0,
        'CE({})'.format(float_format(get_distance1(point_c, point_e) / mm)))

    length_diff3 = (c_point.x - d_point.x) - (g_point.x - h_point.x)
    point7 = (
        (point_e[0] + length_diff3*mm / 2),
        (start_y-brick_height-brick_width/2-brick_height)*mm)

    point8 = (
        (point6[0] - length_diff3*mm / 2),
        (start_y-brick_height-brick_width/2-brick_height)*mm)
    cnv.setDash(6, 3)
    cnv.line(point7[0], point7[1], point8[0], point8[1])
    cnv.drawString(
        point7[0] + 40, point7[1] + 10,
        'GH({})'.format(float_format((point8[0] - point7[0]) / mm)))

    cnv.drawString(
        point_e[0] + 20, point_e[1] - 80,
        'EG({})'.format(float_format(get_distance1(point7, point_e) / mm)))

    # Display horizontal lines.
    cnv.line(point_a[0], point_a[1], point_c[0], point_c[1])
    cnv.line(point_b[0], point_b[1], point_d[0], point_d[1])
    cnv.line(point_c[0], point_c[1], point_e[0], point_e[1])
    cnv.line(point_d[0], point_d[1], point6[0], point6[1])
    cnv.line(point_e[0], point_e[1], point7[0], point7[1])
    cnv.line(point6[0], point6[1], point8[0], point8[1])

    # Show notches for outside to innerside constriction.
    npoint1 = (point_e[0], point_e[1] - inner_outer_diff / 2 * mm)
    npoint2 = (point_e[0] + 20, point_e[1] - inner_outer_diff / 2 * mm)

    npoint3 = (point6[0], point6[1] - inner_outer_diff / 2 * mm)
    npoint4 = (point6[0] - 20, point6[1] - inner_outer_diff / 2 * mm)

    npoint5 = (point7[0], point7[1] + inner_outer_diff / 2 * mm)
    npoint6 = (point7[0] + 20, point7[1] + inner_outer_diff / 2 * mm)

    npoint7 = (point8[0], point8[1] + inner_outer_diff / 2 * mm)
    npoint8 = (point8[0] - 20, point8[1] + inner_outer_diff / 2 * mm)

    cnv.setDash()
    cnv.line(npoint1[0], npoint1[1], npoint2[0], npoint2[1])
    cnv.line(npoint3[0], npoint3[1], npoint4[0], npoint4[1])
    cnv.line(npoint5[0], npoint5[1], npoint6[0], npoint6[1])
    cnv.line(npoint7[0], npoint7[1], npoint8[0], npoint8[1])

    cnv.drawString(
        npoint3[0] - 32,
        npoint3[1] + 6,
        float_format(inner_outer_diff/2))

    # Show vertices.
    cnv.drawString(point_e[0] + 5, point_e[1] + 10, 'E')
    cnv.drawString(point6[0] - 15, point6[1] + 10, 'F')
    cnv.drawString(point7[0] + 5, npoint5[1] + 5, 'G')
    cnv.drawString(point8[0] - 15, npoint5[1] + 5, 'H')

    # Display degree.
    degree = get_degree(point_c, point_a, point_b)
    cnv.drawString(
        point_c[0] + 8,
        point_c[1] + 30,
        u'{}°'.format(float_format(degree)))
    cnv.drawString(
        point_d[0] - 34,
        point_d[1] + 30,
        u'{}°'.format(float_format(degree)))

    cnv.showPage()


def render_row_constriction_template(
        cnv, outer_size, inner_size, length, title, start_y=285):

    start_x = 20
    diff = outer_size - inner_size

    a_point = (start_x*mm, start_y*mm)
    cnv.drawString(a_point[0] + 5, a_point[1] - 15, 'A')

    cnv.drawString(a_point[0] + 60, a_point[1] - 100, title)
    b_point = (
        a_point[0] + length*mm,
        a_point[1] - diff/2*mm)
    cnv.drawString(b_point[0] - 15, b_point[1] - 15, 'B')
    cnv.setDash(6, 3)
    cnv.line(a_point[0], a_point[1], b_point[0], b_point[1])
    cnv.drawString(
        a_point[0] + 60, a_point[1] - 40,
        'AB({})'.format(float_format(get_distance1(a_point, b_point)/mm)))

    c_point = (
        a_point[0],
        a_point[1] - outer_size*mm)
    cnv.drawString(c_point[0] + 5, c_point[1] + 15, 'C')

    cnv.line(a_point[0], a_point[1], c_point[0], c_point[1])
    cnv.drawString(
        c_point[0] + 10, c_point[1] + 80,
        'AC({})'.format(float_format(get_distance1(a_point, c_point)/mm)))

    d_point = (b_point[0], c_point[1] + diff/2*mm)
    cnv.drawString(d_point[0] - 15, d_point[1] + 15, 'D')

    cnv.line(b_point[0], b_point[1], d_point[0], d_point[1])
    cnv.drawString(
        d_point[0] - 60, d_point[1] + 80,
        'BD({})'.format(float_format(get_distance1(b_point, d_point)/mm)))

    cnv.line(c_point[0], c_point[1], d_point[0], d_point[1])
    cnv.drawString(
        c_point[0] + 120, c_point[1] + 10,
        'CD2({})'.format(float_format(get_distance1(c_point, d_point)/mm)))


def render_first_row_template(cnv, first_row, brick_depth):
    start_y = 275
    start_x = 20

    cnv.drawString(
        (start_x - 5)*mm, (start_y + 10)*mm,
        'Warning: verify size with ruller after printing first'
        ' page. Most printers are configured to use scaling.')

    cnv.drawString(
        20, 20,
        'Generated with domebricks.py - https://github.com/nmb10/domebricks')

    point1 = (start_x*mm, start_y*mm)
    cnv.drawString(point1[0] + 5, point1[1] - 15, 'A')

    cnv.drawString(point1[0] + 60, point1[1] - 100, 'Row #1')
    point2 = (
        point1[0] + brick_depth*mm,
        start_y*mm - (first_row.top_inner_point.y - first_row.top_outer_point.y)*mm)  # noqa: E501
    cnv.drawString(point2[0] - 15, point2[1] - 15, 'B')

    cnv.setDash(6, 3)
    cnv.line(point1[0], point1[1], point2[0], point2[1])
    cnv.drawString(
        point1[0] + 60, point1[1] - 40,
        'AB({})'.format(
            float_format(get_distance1(point1, point2)/mm)))

    point3 = (
        point1[0],
        point1[1] - (first_row.bottom_outer_point.y - first_row.top_outer_point.y)*mm)  # noqa: E501
    cnv.drawString(point3[0] + 5, point3[1] + 15, 'C')

    cnv.line(point1[0], point1[1], point3[0], point3[1])
    cnv.drawString(
        point3[0] + 10, point3[1] + 80,
        'AC({})'.format(float_format((point1[1] - point3[1]) / mm)))

    point4 = (point2[0], point3[1])
    cnv.drawString(point4[0] - 15, point4[1] + 15, 'D')

    cnv.line(point2[0], point2[1], point4[0], point4[1])
    cnv.drawString(
        point4[0] - 60, point4[1] + 80,
        'BD({})'.format(float_format((point2[1] - point4[1]) / mm)))

    cnv.line(point3[0], point3[1], point4[0], point4[1])
    cnv.drawString(
        point3[0] + 120, point3[1] + 10,
        'CD1({})'.format(float_format(get_distance1(point4, point3) / mm)))


def build_svg(
        scale=3.78,  # 1 mm == 1mm
        brick_width=250.0,
        brick_height=65.0,
        brick_depth=120.0,
        surface_inner_radius=503.0,
        height=440.0,
        support_template_step=3,
        first_row_height=125.0,
        seam=3.0,
        door_height=265,
        bricks_amount=None,
        minimal_width=40):
    """Returns svg content of a dome.

    Args:
        scale(float, default=3.78): scale of the svg
        brick_width(float): width of the brick
        brick_height(float): height of the brick
        brick_depth(float): depth of the brick
        surface_inner_radius(float, default=503): 503 is about
            diameter=42 inches.
        height(float): height of the dome in the center
        first_row_height(float): height of the soldier brick from first row
        seam(float): seam of the masonry
        bricks_amount(int or None): force bricks amount
            in the row to that value (if possible)
        minimal_width(int): if inner brick size is less then
            that value, brick of the new row will cover 2 bricks
            from the bottom

    Returns:
        str: svg content

    """

    # Params verification.

    if not bricks_amount:
        raise ValueError(
            'Invalid bricks_amount. Expecting > 0.')

    if 100 >= brick_width >= 300:
        raise ValueError(
            'Invalid brick_width. Expecting any from 100 to 300mm')

    if 50 >= brick_height >= 80:
        raise ValueError(
            'Invalid brick_height. Expecting any from 50 to 80mm')

    if 100 >= brick_depth >= 150:
        raise ValueError(
            'Invalid brick_depth. Expecting any from 100 to 150mm')

    if 300 >= surface_inner_radius >= 800:
        raise ValueError(
            'Invalid inner radius. Expecting any from 300 to 800mm')

    if 125 >= height >= 250:
        raise ValueError(
            'Invalid dome height. Expecting any from 125 to 250mm')

    if 4 >= seam >= 8:
        raise ValueError(
            'Invalid dome height. Expecting any from 4 to 8mm')

    # Debugging scales.
    # scale /= 2
    # scale /= 5
    # scale /= 10

    elems = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '''<svg version="1.1"
                width="1500mm"
                height="1000mm"
                xmlns="http://www.w3.org/2000/svg" >''',
        '<g transform="scale({scale})">'
    ]

    warning_part1 = 'Warning: Pre-alfa release of the script. Use it on your own risk, I don\'t'  # noqa: E501
    warning_part2 = 'guarantee correctness of any value computed here.'
    elems.append(
        f'''<text x="100" y="50" font-size="30" fill="brown">
                {warning_part1}
            </text>''')
    elems.append(
        f'''<text x="100" y="86" font-size="30" fill="brown">
                {warning_part2}
            </text>''')

    cx = 200 + surface_inner_radius
    cy = 160 + surface_inner_radius

    # Debug output
    # Inner circle.
    # elems.append(
    #     '<circle cx="{}" cy="{}" r="{}" fill="gray" fill-opacity="0.6"/>'
    #    .format(cx, cy, surface_inner_radius))
    #
    # Outer circle
    # elems.append(
    #     '<circle cx="{}" cy="{}" r="{}" fill="gray" fill-opacity="0.6"/>'
    #     .format(cx, cy, surface_inner_radius + brick_width / 2.0))

    surface_outer_radius = surface_inner_radius + brick_width / 2.0

    # Draw center line.
    radian = math.pi / 2.0
    center_line_x = cx \
        + (surface_inner_radius + brick_width / 2.0 + 100) \
        * math.cos(radian)
    center_line_y = cy \
        - (surface_inner_radius + brick_width / 2.0 - 70) \
        * math.sin(radian)
    elems.append(
        f'''<line x1="{cx}"
                  y1="{cy}"
                  x2="{center_line_x}"
                  y2="{center_line_y}"
                  stroke-width="2"
                  stroke="black" />''')

    surface_circle_center_point = Point('SCCP', cx, cy + 100)
    elems.append(surface_circle_center_point.as_csv(fill='green'))

    radian = math.pi
    previous_row = None

    initial_radian_point = Point(
        'BOP', surface_circle_center_point.x - surface_outer_radius,
        surface_circle_center_point.y)

    # First row starts with width/2, others will be
    # computed based on bricks amount. Doing so to have every
    # seam covered with brick of the next row.
    height_outer_point = Point(
        'HO', surface_circle_center_point.x,
        surface_circle_center_point.y - height - brick_width / 2.0)
    height_inner_point = Point(
        'HI', surface_circle_center_point.x,
        surface_circle_center_point.y - height)

    elems.append(height_inner_point.as_csv())
    elems.append(
        Path(height_inner_point, surface_circle_center_point)
        .as_csv(stroke='green'))

    dome_radius, dome_circle_center_point, first_row_outer_top_point = \
        get_dome_inner_radius(
            surface_circle_center_point, surface_inner_radius,
            brick_width=brick_width, brick_height=brick_height,
            # elems=elems,  # Debug display.
            first_row_height=first_row_height, height=height)

    # Find first row position (soldier row).
    first_row_radian_point = Point(
        'FRRP', first_row_outer_top_point.x, initial_radian_point.y)
    first_row = Row(
        surface_circle_center_point, surface_inner_radius, radian,
        first_row_radian_point, 1,
        vertical=True, outer_height=first_row_height,
        brick_height=brick_height,
        bottom_seam=seam, brick_width=brick_width,
        brick_depth=brick_depth)
    elems.append(first_row_radian_point.as_csv())

    # Show dome bottom
    elems.extend(
        get_floor_elems(
            first_row, surface_circle_center_point,
            surface_inner_radius, brick_height, brick_depth))

    # Cut first row brick by line from outer point to radius center
    line1 = (first_row.top_outer_point, dome_circle_center_point)
    line2 = (first_row.bottom_inner_point, first_row.top_inner_point)

    intersection_point = get_lines_intersection(line1, line2)
    if intersection_point is None:
        # FIXME: Add more details to exception.
        raise ValueError('Lines do not intersect')
    first_row.top_inner_point = intersection_point

    # Debug print:
    # Line1
    # elems.append(
    #    Path(first_row.top_outer_point, dome_circle_center_point)
    #    .as_csv(stroke='green'))
    #
    # Line2
    # elems.append(
    #    Path(first_row.bottom_inner_point, first_row.top_inner_point)
    #    .as_csv(stroke='green'))
    #
    # elems.append(
    #    Path(dome_circle_center_point, height_inner_point)
    #    .as_csv(stroke='green'))
    #
    # elems.append(
    #    Path(first_row.bottom_inner_point, first_row.top_inner_point)
    #    .as_csv(stroke='green'))

    elems.append(
        Path(first_row.top_inner_point, dome_circle_center_point)
        .as_csv(stroke='gray', inner_text=True))

    #
    # Prepare and display brick of (vertical/soldier) row.
    #
    vertical_brick_elems = get_vertical_brick_elems(first_row)
    elems.extend(vertical_brick_elems)

    # Debug:
    # elems.append(
    #     Path(first_row.top_inner_point, dome_circle_center_point).as_csv())
    #
    # Display dome radius circle
    # elems.append(
    #     '''<circle cx="{dome_circle_center_point.x}"
    #                cy="{dome_circle_center_point.y}"
    #                r="{dome_radius}"
    #                stroke-width="3"
    #                stroke="green"
    #                fill-opacity="0.6"/>''')

    # first_row_inner_sizes, first_row_seam = split_row(
    #     first_row, surface_inner_radius, brick_height, seam=seam)
    # first_row_outer_sizes, first_row_seam = split_row(
    #     first_row, surface_inner_radius + brick_width / 2.0,
    #     brick_height, seam=seam)
    y_offset = dome_circle_center_point.y + 100

    # Now compute bricks sizes and create templates pdf.
    # FIXME: Refactor. It's legacy from the version without PDF.
    y_offset += 185
    safety_counter = 0
    rows_counter = 1
    if bricks_amount is not None:
        vertical_seam = seam
    else:
        # Actual value will be computed on first row split.
        vertical_seam = None

        # Actual value will be computed on first row split. Bricks
        # amount may be the same all rows except key brick.
        bricks_amount = None

    inner_radius = surface_inner_radius
    dome_outer_radius = dome_radius
    dome_initial_radian, dome_initial_radian_point = get_dome_radius_radian(
        dome_outer_radius, dome_circle_center_point, first_row,
        brick_width=brick_width)
    # Debug print:
    # elems.append(dome_initial_radian_point.as_csv())

    sizes_row_y_offset = 120

    cnv = canvas.Canvas('row-templates.pdf')
    cnv.setTitle(
        f'Dome bricks templates: inner_radius={inner_radius}, height={height}')
    cnv.setPageSize(size=A4)
    # cnv.translate(mm, mm)

    render_first_row_template(cnv, first_row, brick_depth)

    while True:
        if safety_counter >= 100:
            break
        safety_counter += 1

        if previous_row:
            radian_point = previous_row.top_outer_point
            radian = previous_row.top_radian
        else:
            radian = dome_initial_radian
            radian_point = dome_initial_radian_point
        rows_counter += 1

        bottom_outer_width = brick_depth
        inner_radius = get_distance(
            first_row.top_inner_point, dome_circle_center_point)

        if previous_row \
                and height_outer_point.x - previous_row.top_outer_point.x <= 0:
            # All rows finished. Next is key brick.
            break

        row_instance = Row(
            dome_circle_center_point, inner_radius,
            radian, radian_point, rows_counter,
            vertical=False, brick_height=brick_height,
            outer_height=brick_height,
            bottom_seam=seam, brick_width=brick_width)
        # elems.append(row_instance.bottom_radian_point.as_csv())

        horizontal_outer_top_distance_point = Point(
            f'{rows_counter}', dome_circle_center_point.x,
            row_instance.top_outer_point.y)

        # Display brick points.
        row_brick_elems = row_instance.get_brick_elems()
        elems.extend(row_brick_elems)

        # Show the distance from the top inner corner to center.
        elems.append(
            Path(row_instance.top_inner_point, dome_circle_center_point)
            .as_csv(stroke='gray', inner_text=True))

        row_initial_y = y_offset
        y_offset += 450

        #
        # Prepare cut schemes (sizes and angle)
        #
        horizontal_distance_bottom_point = Point(
            f'#{rows_counter}', dome_circle_center_point.x,
            row_instance.bottom_outer_point.y)
        horizontal_bottom_outer_radius = get_distance(
            row_instance.bottom_outer_point, horizontal_distance_bottom_point)

        if rows_counter == 2 and bricks_amount is None:
            # Compute bricks amount and vertical seam for second
            # (first after soldier) row only. All other rows will
            # have the same amount of bricks (and seams)
            bricks, vertical_seam = split_row(
                row_instance, horizontal_bottom_outer_radius,
                bottom_outer_width, seam=seam)
            bricks_amount = len(bricks)

        top_sizes_x_offset = 80
        a_point = Point(
            'A', top_sizes_x_offset,
            row_initial_y + sizes_row_y_offset)

        if rows_counter > 1:
            # For first row bottom outer side is known
            # (brick_depth), compute it for others.
            horizontal_outer_bottom_distance_point = Point(
                '#{rows_counter}', dome_circle_center_point.x,
                row_instance.bottom_outer_point.y)
            horizontal_outer_bottom_radius = get_distance(
                row_instance.bottom_outer_point,
                horizontal_outer_bottom_distance_point)
            horizontal_outer_bottom_circumference = 2 \
                * math.pi \
                * horizontal_outer_bottom_radius
            bottom_outer_width = round(
                horizontal_outer_bottom_circumference / bricks_amount - vertical_seam,  # noqa: E501
                1)

        b_point = Point(
            'B', top_sizes_x_offset + bottom_outer_width,
            row_initial_y + sizes_row_y_offset)

        ab_center = top_sizes_x_offset + abs(a_point.x - b_point.x) / 2

        # Compute bottom inner side.
        horizontal_inner_bottom_distance_point = Point(
            '#{rows_counter}', dome_circle_center_point.x,
            row_instance.bottom_inner_point.y)
        horizontal_bottom_inner_radius = get_distance(
            row_instance.bottom_inner_point,
            horizontal_inner_bottom_distance_point)
        horizontal_bottom_inner_circumference = 2 \
            * math.pi \
            * horizontal_bottom_inner_radius
        bottom_inner_side = round(
            horizontal_bottom_inner_circumference / bricks_amount - vertical_seam,  # noqa: E501
            1)
        c_point = Point(
            'C', ab_center + bottom_inner_side / 2,
            row_initial_y + sizes_row_y_offset + brick_width / 2.0)

        d_point = Point(
            'D', ab_center - bottom_inner_side / 2,
            row_initial_y + sizes_row_y_offset + brick_width / 2.0)

        # Display template top face.
        horizontal_top_outer_radius = get_distance(
            row_instance.top_outer_point,
            horizontal_outer_top_distance_point)
        # Debug: distance from out to center line.
        # elems.append(
        #     Path(row_instance.top_outer_point,
        #          horizontal_outer_top_distance_point)
        #     .as_csv())
        horizontal_outer_top_circumference = \
            2 \
            * math.pi \
            * horizontal_top_outer_radius
        top_outer_side = round(
            horizontal_outer_top_circumference / bricks_amount - vertical_seam,
            1)

        # Display bottom sizes (for verification after marking)
        bottom_sizes_x_offset = 650
        e_point = Point(
            'E', bottom_sizes_x_offset,
            row_initial_y + sizes_row_y_offset)
        f_point = Point(
            'F', bottom_sizes_x_offset + top_outer_side,
            row_initial_y + sizes_row_y_offset)

        #
        horizontal_inner_top_distance_point = Point(
            f'#{rows_counter}', dome_circle_center_point.x,
            row_instance.top_inner_point.y)
        horizontal_top_inner_radius = get_distance(
            row_instance.top_inner_point, horizontal_inner_top_distance_point)
        horizontal_top_inner_circumference = \
            2 \
            * math.pi \
            * horizontal_top_inner_radius
        top_inner_side = round(
            horizontal_top_inner_circumference / bricks_amount - vertical_seam,
            1)

        ef_center = bottom_sizes_x_offset + abs(e_point.x - f_point.x) / 2

        g_point = Point(
            'G', ef_center + top_inner_side / 2,
            row_initial_y + sizes_row_y_offset + brick_width / 2.0)

        h_point = Point(
            'H', ef_center - top_inner_side / 2,
            row_initial_y + sizes_row_y_offset + brick_width / 2.0)

        # End of paper template.

        if rows_counter == 2:
            # The row above first row is known, so add template to pdf.
            outer_size = get_distance(a_point, b_point) / 2.0 - vertical_seam
            inner_size = get_distance(c_point, d_point) / 2.0 - vertical_seam

            render_row_constriction_template(
                cnv, outer_size, inner_size, brick_depth,
                'Row1',
                start_y=100)
            cnv.showPage()

        # Render row template to pdf file.
        outer_height = brick_height
        inner_height = get_distance(
            row_instance.top_inner_point,
            row_instance.bottom_inner_point)

        inner_outer_diff = outer_height - inner_height

        render_row_brick_template(
            cnv, round(bricks_amount, 1), a_point, b_point, c_point, d_point,
            e_point, f_point, g_point, h_point,
            row_number=rows_counter,
            brick_height=brick_height,
            brick_width=brick_width,
            inner_outer_diff=inner_outer_diff,
            vertical_seam=vertical_seam)

        # FIXME: This is not correct. It should compare
        # h_point-g_point < minimal_width for the next row, not for current.
        if bricks_amount % 2 == 0 \
                and get_distance(h_point, g_point) < minimal_width + 5:
            # Brick is too small, new row will contain
            # larger bricks that will cover 2 bottom bricks.
            bricks_amount = bricks_amount / 2

        # Switch to next row.
        previous_row = row_instance
        if horizontal_top_outer_radius <= brick_width / 2.0:
            # The radius is less then brick length. Further are key bricks.
            break

    outer_size = get_distance(
        row_instance.top_outer_point, row_instance.bottom_outer_point)
    inner_size = get_distance(
        row_instance.top_inner_point, row_instance.bottom_inner_point)

    render_row_constriction_template(
        cnv, outer_size, inner_size, brick_width / 2.0,
        'All except first')
    cnv.save()

    support_template_elems = get_support_template_elems(
        surface_circle_center_point,
        dome_circle_center_point, first_row, height_inner_point, row_instance,
        seam=seam, template_width=surface_inner_radius, template_height=height,
        support_template_step=support_template_step)

    elems.extend(support_template_elems)

    # Show key brick template.
    # FIXME: Implement
    # y_offset += 300
    # elems.extend(
    #     get_key_brick_templates(
    #         key_brick_radius4, get_distance(h_point, g_point),
    #         y_offset, brick_width=brick_width))

    elems.append('</g></svg>')

    total_layout = '\n'.join([str(x) for x in elems])
    with open('dome.svg', 'w') as f:
        f.write(total_layout)

    # Create viewbox copy for every brick.
    return total_layout


def get_distance(p1, p2):
    """Returns distance between two points."""
    distance = math.sqrt(((p1.x - p2.x) ** 2) + ((p1.y - p2.y) ** 2))
    return round(distance, 1)


def get_distance1(p1, p2):
    """Returns distance between two points."""
    distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
    return round(distance, 1)


def split_row(row_instance, radius, elem_width, seam=3):
    # Find how many full bricks we need to fit that row.
    radian_pivot = 0
    bricks_amount = 0
    step = 0.0001
    bricks = []
    brick_cut = 0
    vertical_seam = seam

    dome_circle_center_point = Point('DCCP', 900, 2200)
    # elems.append(dome_circle_center_point.as_csv())
    # elems.append(
    #    '''<circle cx="900" cy="2200"
    #               r="{horizontal_bottom_outer_radius}"
    #               fill="blue"
    #               fill-opacity="0.6"/>')
    previous_brick_point = Point(
        '?', dome_circle_center_point.x + radius,
        dome_circle_center_point.y)
    # elems.append(previous_brick_point.as_csv(fill='black'))
    while True:
        if radian_pivot >= 2 * math.pi:
            break
        new_x = dome_circle_center_point.x + radius * math.cos(radian_pivot)
        new_y = dome_circle_center_point.y - radius * math.sin(radian_pivot)
        new_point = Point('?', new_x, new_y)
        brick_cut = get_distance(previous_brick_point, new_point)
        if brick_cut >= elem_width + vertical_seam:
            bricks_amount += 1
            # elems.append(new_point.as_csv())
            # elems.append(Path(previous_brick_point, new_point).as_csv())
            # elems.append(Path(dome_circle_center_point, new_point).as_csv())
            previous_brick_point = new_point
            bricks.append(brick_cut - vertical_seam)
        radian_pivot += step
    if brick_cut:
        # Small cut of brick remained. Make it full by taking sizes from every
        # brick in the row.
        size_to_take = (elem_width - brick_cut) / len(bricks)
        bricks = [(x - size_to_take) for x in bricks]
        bricks.append(brick_cut + len(bricks) * size_to_take - size_to_take)
        # vertical_seam = round(vertical_seam + brick_cut / len(bricks), 1)
    return bricks, vertical_seam


def get_lines_intersection(line1, line2):
    """Returns point where two lines intersects. Otherwise None."""
    # https://stackoverflow.com/a/20677983/247075
    xdiff = (line1[0].x - line1[1].x, line2[0].x - line2[1].x)
    ydiff = (line1[0].y - line1[1].y, line2[0].y - line2[1].y)

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return None

    d = (det(line1[0].as_tuple(), line1[1].as_tuple()),
         det(line2[0].as_tuple(), line2[1].as_tuple()))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return Point('I', x, y)


def get_dome_radius_radian(
        dome_outer_radius, dome_circle_center,
        first_row, brick_width=250):
    """Returns dome radian and point where the radian placed."""

    # First row has radian for surface radius. But for
    # second row we need radian for dome radius. AKA switching
    # plane from horizontal radius to vertical radius.

    outer_point = get_point_on_line(
        first_row.top_inner_point, first_row.top_outer_point,
        distance=brick_width / 2.0, title='T')

    radian = get_points_radian(dome_circle_center, outer_point)
    return radian, outer_point


def get_point_on_line(point1, point2, distance=70.0, title='T'):
    # https://math.stackexchange.com/questions/175896/finding-a-point-along-a-line-a-certain-distance-away-from-another-point
    start_end_point_dist = math.sqrt(
        pow(point2.x - point1.x, 2) + pow(point2.y - point1.y, 2))
    ratio = distance / start_end_point_dist
    xt = (1 - ratio) * point1.x + ratio * point2.x
    yt = (1 - ratio) * point1.y + ratio * point2.y
    new_point = Point(title, xt, yt)
    return new_point


def float_format(number):
    return str(round(number, 1))


def get_dome_inner_radius(
        surface_circle_center_point, surface_inner_radius,
        brick_width=250, brick_height=65, elems=None, first_row_height=160,
        height=450):
    """Returns inner radius for dome."""

    # Note first row outer top point will change while computing dome radius.
    first_row_outer_top_point = Point(
        'RO#1',
        surface_circle_center_point.x - surface_inner_radius - brick_width / 2,
        surface_circle_center_point.y - first_row_height + brick_height)
    first_row_inner_bottom_point = Point(
        'RI#1',
        surface_circle_center_point.x - surface_inner_radius,
        surface_circle_center_point.y)
    height_inner_point = Point(
        'H1',
        surface_circle_center_point.x,
        surface_circle_center_point.y - height)
    height_outer_point = Point(
        'HO1',
        surface_circle_center_point.x,
        surface_circle_center_point.y - height - brick_width / 2.0)

    # Find center of the dome circle - move down from the height until the
    # distance will be the same.
    counter = 0
    step = 1  # mm
    new_first_row_outer_top_point = None
    while True:
        # We compute it by outer point because
        # inner point will be lower because of cut.
        pivot_point = Point(
            'DSCP', height_inner_point.x, height_inner_point.y + step)

        #
        # Verify outer point is covered by next row, otherwise
        # move the outer point.
        # FIXME: Find a math instead of a loop
        # Find a point on the inner side of the soldier brick.
        for i in range(int(math.ceil(brick_width * 2))):
            temp_inner_point = get_point_on_line(
                first_row_outer_top_point, pivot_point, distance=i)
            if temp_inner_point.x >= first_row_inner_bottom_point.x:
                # if step % 25 == 0:
                #     elems.append(temp_inner_point.as_csv())
                #     elems.append(
                #          Path(first_row_outer_top_point, pivot_point)
                #          .as_csv())
                break

        if get_distance(
                first_row_outer_top_point,
                temp_inner_point) >= brick_width / 2.0:
            dist = \
                get_distance(first_row_outer_top_point, temp_inner_point) \
                - brick_width \
                / 2.0
            moved_first_row_outer_top_point = get_point_on_line(
                first_row_outer_top_point, pivot_point, distance=dist)
            new_first_row_outer_top_point = moved_first_row_outer_top_point

        diff = int(get_distance(pivot_point, new_first_row_outer_top_point)) \
            - int(get_distance(pivot_point, height_outer_point))
        is_circle_center = abs(diff) <= 1
        if is_circle_center:
            dome_circle_center_point = pivot_point
            break

        if counter >= 6000:
            # Sanity check.
            raise RuntimeError(
                'Could not find center of the inner radius for dome.')
        counter += 1
        step += 1
    if elems:
        elems.append(first_row_outer_top_point.as_csv())
        elems.append(dome_circle_center_point.as_csv())

    dome_radius = get_distance(
        dome_circle_center_point, first_row_outer_top_point)
    if new_first_row_outer_top_point:
        return (dome_radius, dome_circle_center_point,
                new_first_row_outer_top_point)
    return dome_radius, dome_circle_center_point, first_row_outer_top_point


def get_degree(a_point, b_point, c_point):
    # Returns degree of the corner. b_point is a vertice.

    # Create new triangle with right corner, it's hypo is b-a
    right_triangle_vertice_point = (b_point[0], a_point[1])

    # Now we know 3 vertices of the right corner. Find degree.
    hypotenuse = get_distance1(b_point, a_point)

    # Since right_triangle_vertice_point-b_point-a_point is
    # right triangle we can compute its degree
    # Debug output
    # elems.append(Path(degree_point_a, degree_point_d).as_csv())
    degree1 = math.degrees(
        math.asin(
            get_distance1(
                right_triangle_vertice_point,
                a_point) / hypotenuse))

    degree2 = 90.0 - degree1
    return degree2


def get_support_template_elems(
        surface_circle_center_point, dome_circle_center_point,
        first_row, height_inner_point, row_instance,
        template_width=None, template_height=None,
        seam=4, support_template_step=3):

    assert template_width is not None
    assert template_height is not None
    elems = []
    template_radius = get_distance(
        first_row.top_inner_point,
        dome_circle_center_point)
    template_x_offset = height_inner_point.x  # - 176  # (Note: useful for debugging. Moves the template outside of the dome center)  # noqa: E501
    # FIXME: Why `-1`?
    blank_top_left = Point(
        'BTL', template_x_offset, row_instance.top_inner_point.y - 1)
    blank_top_right = Point(
        'BTR', template_x_offset + template_width, blank_top_left.y)
    blank_bottom_right = Point(
        'BBR', template_x_offset + template_width,
        # height_inner_point.y + template_height)
        surface_circle_center_point.y)
    blank_bottom_left = Point(
        'BBL', template_x_offset,
        # height_inner_point.y + template_height)
        surface_circle_center_point.y)

    support_radius_center_point = Point(
        'SRCP', blank_bottom_left.x, dome_circle_center_point.y)
    # Debug output:
    # elems.append(
    #     Path(support_radius_center_point, blank_bottom_left)
    #     .as_csv())
    # elems.append(
    #     Path(blank_bottom_right, support_radius_center_point)
    #     .as_csv())
    elems.append(support_radius_center_point.as_csv())

    elems.append(
        Path(blank_top_left, blank_top_right, distance='')
        .as_csv(stroke='red', dasharray=True))
    elems.append(
        Path(blank_top_right, blank_bottom_right)
        .as_csv(stroke='red', dasharray=True, outside_path=True,
                x_offset=40, y_offset=template_height / 2.0, rotate=40))
    elems.append(
        Path(blank_bottom_left, blank_top_left)
        .as_csv(stroke='red', dasharray=True))
    elems.append(
        Path(blank_bottom_left, blank_bottom_right)
        .as_csv(stroke='red', dasharray=True, outside_path=True,
                x_offset=template_radius / 2.0, y_offset=70))
    elems.append(
        Path(support_radius_center_point, blank_top_left)
        .as_csv(stroke='red', dasharray=True, outside_path=True,
                y_offset=-template_height / 2.0, x_offset=-30, rotate=-90))
    # Debug print: corners of the blank of the template
    # elems.append(blank_top_left.as_csv())
    # elems.append(blank_top_right.as_csv())
    # elems.append(blank_bottom_right.as_csv())
    # elems.append(blank_bottom_left.as_csv())

    # Now display the cut over the blank needed to get actual template.

    # First find the point where the cut starts - it's
    # soldier brick inner top point
    template_radian_counter = 0
    template_radian_step = 0.0001
    first_point = Point(
        'FP', blank_bottom_right.x, first_row.top_inner_point.y)
    # debug output
    # elems.append(first_point.as_csv())
    while True:
        if template_radian_counter >= math.pi / 2.0:
            break

        new_x = support_radius_center_point.x \
            + template_radius \
            * math.cos(template_radian_counter)
        new_y = support_radius_center_point.y \
            - template_radius \
            * math.sin(template_radian_counter)
        if new_y <= first_point.y:
            # print('Region of the blank found.')
            break

        template_radian_counter += template_radian_step
    # Now display points of the cut on the blank.
    previous_point = None
    # Since it's a circle we assume rows height is the same, so we can use the
    # inner height from any row.
    row_inner_height = \
        get_distance(
            row_instance.bottom_inner_point,
            row_instance.top_inner_point) \
        + seam
    point_counter = 1
    colors = [
        'maroon',
        'red',
        'purple',
        'fuchsia',
        'green',
        'lime',
        'olive',
        'navy',
        'blue',
        'teal'
    ]
    while True:
        if template_radian_counter >= math.pi / 2.0:
            break

        if point_counter > row_instance.number + 1:
            break

        new_x = support_radius_center_point.x \
            + template_radius \
            * math.cos(template_radian_counter)
        new_y = support_radius_center_point.y \
            - template_radius \
            * math.sin(template_radian_counter)
        is_last_point = new_x <= blank_top_left.x

        new_point = Point(str(point_counter), new_x, new_y)
        point_color = colors[point_counter % 10]

        if previous_point:
            if get_distance(new_point, previous_point) >= row_inner_height \
                    or is_last_point:

                if point_counter == row_instance.number + 1:
                    # last row.
                    cut_point = Point(
                        'C', blank_top_left.x, new_point.y)
                else:
                    cut_point = Point(
                        'C', new_point.x - row_inner_height, new_point.y)
                if support_template_step >= 3:
                    if point_counter == 2:
                        # Display cut distance only once (it
                        # always equals to row inner height)
                        elems.append(
                            Path(new_point, previous_point)
                            .as_csv(dasharray=True, stroke='red'))
                    else:
                        elems.append(
                            Path(new_point, previous_point, distance='')
                            .as_csv(dasharray=True, stroke='red'))
                    elems.append(
                        Path(cut_point, new_point, distance=' ')
                        .as_csv(dasharray=True, stroke='red'))
                # Show point on left vertical side of the blank
                # Debug print - line from SRCP to the point
                # elems.append(
                #    Path(new_point, support_radius_center_point).as_csv())
                previous_point = new_point

                if support_template_step >= 2:
                    elems.append(
                        new_point
                        .as_csv(fill=colors[point_counter % 10]))

                vertical_line_top = Point(
                    '', new_point.x, blank_top_left.y)
                elems.append(vertical_line_top.as_csv())

                vertical_line_bottom_point = Point(
                    '', new_point.x, blank_bottom_left.y)
                elems.append(vertical_line_bottom_point.as_csv())

                elems.append(
                    Path(vertical_line_top, blank_top_left)
                    .as_csv(dasharray=True, opacity=0, outside_path=True,
                            rotate=-20, y_offset=-10, x_offset=-10))
                elems.append(
                    Path(vertical_line_bottom_point, blank_bottom_left)
                    .as_csv(dasharray=True, opacity=0, outside_path=True,
                            rotate=30, y_offset=34))
                if support_template_step >= 2:
                    elems.append(
                        Path(vertical_line_top, new_point)
                        .as_csv(stroke=point_color, outside_path=True,
                                rotate=40, y_offset=36, x_offset=10))
                    elems.append(vertical_line_bottom_point.as_csv())
                    elems.append(
                        new_point
                        .as_csv(fill=colors[point_counter % 10]))
                    # elems.append(
                    #     Path(vertical_line_bottom_point, new_point)
                    #     .as_csv(stroke=colors[point_counter % 10],
                    #             outside_path=True,
                    #             rotate=40, y_offset=-36, x_offset=6))

                if support_template_step >= 3:
                    screw1_point = get_point_on_line(
                        new_point, support_radius_center_point, title='')
                    elems.append(screw1_point.as_csv())
                    elems.append(
                        Path(screw1_point, new_point)
                        .as_csv(stroke=point_color))

                    screw2_point = get_point_on_line(
                        new_point, support_radius_center_point,
                        distance=180, title='')
                    elems.append(screw2_point.as_csv())

                    # Display geometry to find screw points.
                    temp_point1 = Point(
                        'XXX', support_radius_center_point.x, screw2_point.y)
                    temp_path1 = Path(screw2_point, temp_point1)
                    elems.append(
                        temp_path1
                        .as_csv(stroke=point_color, rotate=180, y_offset=-24))

                    temp_point2 = Point(
                        'XXXX', screw2_point.x, surface_circle_center_point.y)
                    temp_path2 = Path(temp_point2, screw2_point)
                    elems.append(
                        temp_path2
                        .as_csv(stroke=point_color, y_offset=-10))

                    temp_path3 = Path(screw2_point, screw1_point)
                    elems.append(temp_path3.as_csv(stroke=point_color))
                # Point displayed
                point_counter += 1
        else:
            cut_point = Point('C', new_point.x - row_inner_height, new_point.y)
            if support_template_step >= 2:
                elems.append(new_point.as_csv())
                elems.append(
                    Path(blank_bottom_right, new_point)
                    .as_csv(opacity=0, outside_path=True,
                            y_offset=-36, rotate=40, x_offset=8))
                elems.append(
                    Path(blank_top_right, new_point)
                    .as_csv(opacity=0, outside_path=True,
                            y_offset=96, rotate=40, x_offset=8))
            if support_template_step >= 3:
                elems.append(
                    Path(cut_point, new_point, distance=' ')
                    .as_csv(dasharray=True, stroke='red'))

                # FIXME: remove copy-paste
                # elems.append(
                #     Path(support_radius_center_point, new_point, distance='')
                #     .as_csv(stroke='gray'))
                screw1_point = get_point_on_line(
                    new_point, support_radius_center_point, title='')
                elems.append(screw1_point.as_csv())
                elems.append(
                    Path(screw1_point, new_point)
                    .as_csv(stroke=point_color))

                screw2_point = get_point_on_line(
                    new_point, support_radius_center_point,
                    distance=180, title='')
                elems.append(screw2_point.as_csv())

                # Display geometry to find screw points.
                temp_point1 = Point(
                    'XXX', support_radius_center_point.x, screw2_point.y)
                temp_path1 = Path(screw2_point, temp_point1)
                elems.append(
                    temp_path1
                    .as_csv(stroke=point_color, rotate=180, y_offset=-24))

                temp_point2 = Point(
                    'XXXX', screw2_point.x, surface_circle_center_point.y)
                temp_path2 = Path(screw2_point, temp_point2)
                elems.append(
                    temp_path2
                    .as_csv(stroke=point_color, y_offset=-10))

                temp_path3 = Path(screw2_point, screw1_point)
                elems.append(temp_path3.as_csv(stroke=point_color))
            previous_point = new_point
            point_counter += 1

        if is_last_point:
            break
        template_radian_counter += template_radian_step
    return elems


def get_key_brick_templates(radius, side, y_offset, brick_width=250):
    elems = []
    x_offset = 150
    key_brick1_a = Point(
        'A', x_offset, y_offset)
    key_brick1_b = Point(
        'B', x_offset + brick_width, y_offset)
    key_brick1_c = Point(
        'C', x_offset + brick_width, y_offset + brick_width / 2.0)
    key_brick1_d = Point(
        'D', x_offset, y_offset + brick_width / 2.0)
    elems.append(key_brick1_a.as_csv())
    elems.append(key_brick1_b.as_csv())
    # elems.append(key_brick1_c.as_csv())
    # elems.append(key_brick1_d.as_csv())
    elems.append(
        Path(key_brick1_a, key_brick1_b)
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick1_b, key_brick1_c)
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick1_c, key_brick1_d)
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick1_d, key_brick1_a, distance=' ')
        .as_csv(stroke='orange'))

    key_brick2_a = Point(
        'A', x_offset, y_offset + brick_width / 2.0 + 6)
    key_brick2_b = Point(
        'B', x_offset + brick_width, y_offset + brick_width / 2.0 + 6)
    key_brick2_c = Point(
        'C', x_offset + brick_width, y_offset + brick_width + 6)
    key_brick2_d = Point(
        'D', x_offset, y_offset + brick_width + 6)
    # elems.append(key_brick2_a.as_csv())
    # elems.append(key_brick2_b.as_csv())
    elems.append(key_brick2_c.as_csv())
    elems.append(key_brick2_d.as_csv())
    elems.append(
        Path(key_brick2_a, key_brick2_b, distance=' ')
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick2_b, key_brick2_c)
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick2_c, key_brick2_d)
        .as_csv(stroke='orange'))
    elems.append(
        Path(key_brick2_d, key_brick2_a, distance=' ')
        .as_csv(stroke='orange'))

    key_brick_center = Point(
        'O', key_brick1_d.x + radius,
        key_brick1_d.y + 3)
    elems.append(key_brick_center.as_csv())
    # elems.append(
    #    Path(center_line_point, key_brick_center)
    #    .as_csv(stroke='black'))

    # Display key bricks cut points
    key_brick_radian = 0
    key_brick_radian_step = 0.005
    previous_point = None
    template_shown = False
    while True:
        if key_brick_radian >= 2 * math.pi:
            break

        new_x = key_brick_center.x + radius * math.cos(key_brick_radian)
        new_y = key_brick_center.y - radius * math.sin(key_brick_radian)
        new_point = Point('?', new_x, new_y)
        if previous_point:
            if get_distance(new_point, previous_point) >= side:
                if not template_shown:
                    elems.append(
                        Path(new_point, previous_point).as_csv())
                    elems.append(
                        Path(new_point, key_brick_center).as_csv())
                    elems.append(
                        Path(previous_point, key_brick_center).as_csv())
                    template_shown = True
                previous_point = new_point
                elems.append(new_point.as_csv())
        else:
            previous_point = new_point
            elems.append(new_point.as_csv())

        key_brick_radian += key_brick_radian_step
    return elems


def get_vertical_brick_elems(first_row):
    elems = []
    bottom_outer_point = Point(
        'Soldier-A', first_row.bottom_outer_point.x,
        first_row.bottom_outer_point.y)
    bottom_inner_point = Point(
        'Soldier-B', first_row.bottom_inner_point.x,
        first_row.bottom_outer_point.y)
    elems.append(
        Path(bottom_outer_point, first_row.top_outer_point)
        .as_csv(stroke='orange'))
    elems.append(
        Path(first_row.top_outer_point, first_row.top_inner_point)
        .as_csv(stroke='orange', inner_text=True))
    elems.append(
        Path(first_row.top_inner_point, bottom_inner_point)
        .as_csv(stroke='orange', inner_text=True))

    elems.append(
        Path(bottom_inner_point, bottom_outer_point)
        .as_csv(stroke='orange', inner_text=True))
    return elems


def to_polar(x, y):
    """Converts from cartesian to polar."""
    # r = √ (122 + 52)
    rho = math.sqrt(x ** 2 + y ** 2)
    phi = math.degrees(math.atan2(y, x))
    return (rho, phi)


def to_cart(rho, phi):
    """Converts from polar to cartesian."""
    # For x - cos(degrees) = x / radius
    new_x = rho * math.cos(math.radians(phi))

    # For y -  sin(degrees) = y / radius
    new_y = rho * math.sin(math.radians(phi))
    return (new_x, new_y)


def move_along_radius(radian_point=None, radius=None,
                      circle_center_point=None, distance=None):
    """Returns radian and radian point after moving them to given distance.
    Args:
        radian_point(Point): point of the redian on circle surface
        circle_center_point(Point): center point of the circle
        distance (int): distance where to move
        radius (int): radius of the circle.

    Returns:
        tuple(new_radian (int), new_radian_point (int)):
    """
    assert radian_point is not None, 'radian_point param is required'
    assert radius is not None, 'radius param is required'
    assert circle_center_point is not None, \
        'circle_center_point param is required'
    assert distance is not None, 'distance param is required'

    #
    # To achieve move by distance (aka chord length) we
    # switch from cartesian to polar system, move to distance
    # and return to cartesian system.
    #

    # Move point coordinates to origin (0, 0) to conform to polar system
    # origin (which is 0,0)
    x1 = radian_point.x - circle_center_point.x
    y1 = radian_point.y - circle_center_point.y

    # Find polar coordinates around (0, 0)
    polar = to_polar(x1, y1)

    # Find degree of angle opposite to distance (chord).
    a = distance
    b = polar[0]
    c = polar[0]
    distance_cos = (b ** 2 + c ** 2 - a ** 2) / (2 * b * c)
    distance_angle = math.degrees(math.acos(distance_cos))

    new_point_polar = (polar[0], distance_angle + polar[1])

    # Convert to cartesian
    new_x, new_y = to_cart(*new_point_polar)

    # Now place new point around circle center point
    new_x += circle_center_point.x
    new_y += circle_center_point.y
    new_point = Point('', new_x, new_y)

    # And compute new radian.
    new_radian = get_points_radian(circle_center_point, new_point)
    return new_radian, new_point


def get_points_radian(circle_center_point, point):
    """Returns radian for two points."""
    hypotenuse = get_distance(circle_center_point, point)
    right_angle_point = Point('?', point.x, circle_center_point.y)
    adjacent = get_distance(right_angle_point, point)
    new_radian = math.pi - math.asin(adjacent / hypotenuse)
    return new_radian


def get_floor_elems(first_row, surface_circle_center_point,
                    surface_inner_radius, brick_height, brick_depth):
    elems = []

    gap = 8  # gap between dome bottom and soldier bricks.

    # y is the same for all top and bottom bricks
    y_top = surface_circle_center_point.y
    y_bottom = first_row.bottom_inner_point.y

    # First brick.
    brick1_top_left = Point('', first_row.bottom_inner_point.x + gap, y_top)
    # brick1_top_left = Point(
    #     '', first_row.bottom_inner_point.x + gap,
    #     first_row.bottom_inner_point.y - brick_height)
    brick1_top_right = Point('', brick1_top_left.x + brick_depth, y_top)
    brick1_bottom_right = Point('', brick1_top_right.x, y_bottom)
    brick1_bottom_left = Point('', brick1_top_left.x, y_bottom)

    elems.append(
        Path(brick1_top_left, brick1_top_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick1_top_right, brick1_bottom_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick1_bottom_right, brick1_bottom_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick1_bottom_left, brick1_top_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    # Second brick.
    brick2_top_left = Point('', brick1_top_right.x + 3, y_top)
    brick2_top_right = Point('', brick2_top_left.x + brick_depth, y_top)
    brick2_bottom_right = Point('', brick2_top_left.x + brick_depth, y_bottom)
    brick2_bottom_left = Point('', brick2_top_left.x, y_bottom)

    elems.append(
        Path(brick2_top_left, brick2_top_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick2_top_right, brick2_bottom_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick2_bottom_right, brick2_bottom_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick2_bottom_left, brick2_top_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    # Third brick.
    brick3_top_left = Point('', brick2_top_right.x + 3, y_top)
    brick3_top_right = Point('', brick3_top_left.x + brick_depth, y_top)
    brick3_bottom_right = Point('', brick3_top_right.x, y_bottom)
    brick3_bottom_left = Point('', brick3_top_left.x, y_bottom)

    elems.append(
        Path(brick3_top_left, brick3_top_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick3_top_right, brick3_bottom_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick3_bottom_right, brick3_bottom_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick3_bottom_left, brick3_top_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    # Thourth brick.
    brick4_top_left = Point('', brick3_top_right.x + 3, y_top)
    brick4_top_right = Point('', brick4_top_left.x + brick_depth, y_top)
    brick4_bottom_right = Point('', brick4_top_right.x, y_bottom)
    brick4_bottom_left = Point('', brick4_top_left.x, y_bottom)

    elems.append(
        Path(brick4_top_left, brick4_top_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick4_top_right, brick4_bottom_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick4_bottom_right, brick4_bottom_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick4_bottom_left, brick4_top_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    # Thifth brick.
    brick5_top_left = Point('', brick4_top_right.x + 3, y_top)
    brick5_top_right = Point('', brick5_top_left.x + brick_depth, y_top)
    brick5_bottom_right = Point('', brick5_top_right.x, y_bottom)
    brick5_bottom_left = Point('', brick5_top_left.x, y_bottom)

    elems.append(
        Path(brick5_top_left, brick5_top_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick5_top_right, brick5_bottom_right, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick5_bottom_right, brick5_bottom_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    elems.append(
        Path(brick5_bottom_left, brick5_top_left, distance=' ')
        .as_csv(
            stroke='orange', outside_path=True,
            x_offset=surface_inner_radius / 2.0, y_offset=30))

    return elems


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--scale', default=3.78,
        type=float,
        help='Scale of the svg.')
    parser.add_argument(
        '--brick_width', default=250,
        type=int,
        help='Brick width (mm.)')
    parser.add_argument(
        '--brick_height', default=65,
        type=int,
        help='Brick height (mm.)')
    parser.add_argument(
        '--brick_depth', default=120,
        type=int,
        help='Brick depth (mm.)')
    parser.add_argument(
        '--inner_radius', default=503,
        type=int,
        help='Inner surface radius (mm.)')
    parser.add_argument(
        '--height', default=440,
        type=int,
        help='Dome height (mm.)'),
    parser.add_argument(
        '--first_row_height', default=208,
        type=int,
        help='First row outer height (mm)')
    parser.add_argument(
        '--seam', default=3,
        type=int,
        help='Masonry seam (mm.)')
    parser.add_argument(
        '--door_height', default=265,
        type=int,
        help='Door height(mm.)')
    parser.add_argument(
        '--bricks-amount', default=None,
        type=int,
        help='How many bricks in a row')
    parser.add_argument(
        '--minimal-width', default=None,
        type=int,
        help='If row brick inner bottom side is less then that'
             ' value (roughly), build next row with bricks'
             ' that cover bottom 2 bricks.')

    args = parser.parse_args()
    build_svg(
        scale=args.scale,
        brick_width=args.brick_width,
        brick_height=args.brick_height,
        brick_depth=args.brick_depth,
        surface_inner_radius=args.inner_radius,
        height=args.height,
        first_row_height=args.first_row_height,
        seam=args.seam,
        door_height=args.door_height,
        bricks_amount=args.bricks_amount,
        minimal_width=40)
    print('Done. Check dome.svg and row-templates.pdf.')
