from unittest import TestCase, main as unittest_main
from domebricks import Point, Path, Row, \
    get_distance, get_lines_intersection, get_dome_radius_radian, get_point_on_line, \
    get_dome_inner_radius, get_degree_elements
from mock import Mock


def debug_dump(test_function):
    """Writes test output to svg file for better debugging."""
    def inner(test_instance):
        output, elems = test_function(test_instance)
        if output:
            dump_svg(elems)
    return inner


class PointTest(TestCase):

    def test_point_instance(self):
        point1 = Point('point1', 100, 101)
        self.assertEqual(point1.x, 100)
        self.assertEqual(point1.y, 101)
        csv_content = point1.as_csv()
        self.assertIn('<text fill="green" x="80" y="91">', csv_content)


class PathTest(TestCase):

    def test_path_instance(self):
        point1 = Point('point1', 100, 101)
        point2 = Point('point2', 200, 202)
        path1 = Path(point1, point2)

        csv_content = path1.as_csv()
        self.assertIn('<path id="path', csv_content)


class RowTest(TestCase):

    @debug_dump
    def test_vertical_row(self):
        # vertical aka soldier - the first row of the dome.

        surface_circle_center_point = Point('SCCP', 703, 663)
        surface_inner_radius = 500
        radian = 3.14
        first_row_radian_point = Point('FRRP', 84, 663)
        vertical_row = Row(
            surface_circle_center_point, surface_inner_radius, radian,
            first_row_radian_point, 1,
            vertical=True, brick_height=120)

        self.assertAlmostEqual(vertical_row.top_outer_point.x, 78.0, delta=0.01)
        self.assertAlmostEqual(vertical_row.top_outer_point.y, 542.02, delta=0.01)

        self.assertAlmostEqual(vertical_row.top_inner_point.x, 203.0, delta=0.01)
        self.assertAlmostEqual(vertical_row.top_inner_point.y, 566.21, delta=0.01)

        # FIXME: Verify bottom points math.
        debug_elems = [
            surface_circle_center_point.as_csv(),
            first_row_radian_point.as_csv(),
            vertical_row.bottom_outer_point.as_csv(),
            vertical_row.top_outer_point.as_csv(),
            vertical_row.bottom_inner_point.as_csv(),
            vertical_row.top_inner_point.as_csv(),
            Path(vertical_row.bottom_outer_point, surface_circle_center_point)
            .as_csv(stroke='red', dasharray=True),
            Path(vertical_row.top_outer_point, surface_circle_center_point)
            .as_csv(stroke='red', dasharray=True),
        ]
        return True, debug_elems


class GetDistanceTest(TestCase):

    def test_returns_vertical_distance_between_two_points(self):
        p1 = Point('', 0, 0)
        p2 = Point('', 0, 10)
        ret = get_distance(p1, p2)

        self.assertEqual(ret, 10)

    def test_returns_horizontal_distance_between_two_points(self):
        p1 = Point('', 0, 0)
        p2 = Point('', 12, 0)
        ret = get_distance(p1, p2)

        self.assertEqual(ret, 12)

    def test_returns_diagonal_distance_between_two_points(self):
        p1 = Point('', 0, 0)
        p2 = Point('', 10, 10)
        ret = get_distance(p1, p2)

        self.assertEqual(ret, 14.1)


class SplitRowTest(TestCase):
    pass


class GetLinesIntersectionTest(TestCase):

    def test_returns_none_if_no_intersection(self):
        line1 = (Point('', 0, 0), Point('', 0, 10))
        line2 = (Point('', 2, 0), Point('', 2, 10))
        ret = get_lines_intersection(line1, line2)
        self.assertIsNone(ret)

    @debug_dump
    def test_returns_intersection_point_perpendicular_lines(self):
        horizontal_line = (Point('HL1', 150, 100), Point('HL2', 250, 100))
        vertical_line = (Point('VL1', 90, 30), Point('VL2', 90, 50))
        intersection_point = get_lines_intersection(vertical_line, horizontal_line)
        self.assertIsNotNone(intersection_point)

        self.assertEqual(intersection_point.x, 90.0)
        self.assertEqual(intersection_point.y, 100.0)

        elems = [Path(horizontal_line[0], horizontal_line[1]).as_csv(),
                 Path(vertical_line[0], vertical_line[1]).as_csv(),
                 intersection_point.as_csv()]
        return False, elems

    @debug_dump
    def test_returns_intersection_point_converged_lines(self):
        horizontal_line = (Point('HL1', 150, 100), Point('HL2', 250, 120))
        vertical_line = (Point('VL1', 60, 30), Point('VL2', 90, 70))
        intersection_point = get_lines_intersection(vertical_line, horizontal_line)
        self.assertIsNotNone(intersection_point)
        self.assertAlmostEqual(intersection_point.x, 105.88, delta=0.01)
        self.assertAlmostEqual(intersection_point.y, 91.17, delta=0.01)

        # Debug output
        elems = [Path(horizontal_line[0], horizontal_line[1]).as_csv(),
                 Path(vertical_line[0], vertical_line[1]).as_csv(),
                 intersection_point.as_csv()]
        return False, elems

    @debug_dump
    def test_returns_intersection_point_intersected_lines(self):
        green_line = (Point('HL1', 70, 100), Point('HL2', 250, 120))
        red_line = (Point('VL1', 60, 30), Point('VL2', 120, 170))
        intersection_point = get_lines_intersection(green_line, red_line)
        self.assertIsNotNone(intersection_point)
        self.assertAlmostEqual(intersection_point.x, 91, delta=0.01)
        self.assertAlmostEqual(intersection_point.y, 102.33, delta=0.01)

        # Debug output
        elems = [Path(green_line[0], green_line[1]).as_csv(stroke='green'),
                 Path(red_line[0], red_line[1]).as_csv(stroke='red'),
                 intersection_point.as_csv()]
        return False, elems


class GetDomeRadiusRadianTest(TestCase):

    @debug_dump
    def test_moves_radian_point_to_halfed_brick_width(self):
        dome_outer_radius = 100
        dome_circle_center_point = Point('DCP', 550, 250)

        first_row = Mock()
        first_row.top_outer_point = Point('TOP', 150, 250)
        first_row.top_inner_point = Point('TIP', 300, 250)

        radian, radian_point = get_dome_radius_radian(
            dome_outer_radius, dome_circle_center_point, first_row,
            brick_width=250)

        self.assertEqual(first_row.top_inner_point.x - radian_point.x, 125)
        self.assertAlmostEqual(radian, 3.14, delta=0.01)

        dump_elems = [
            dome_circle_center_point.as_csv(),
            first_row.top_inner_point.as_csv(),
            first_row.top_outer_point.as_csv(),
            radian_point.as_csv()]
        return False, dump_elems


class GetPointOnLineTest(TestCase):

    @debug_dump
    def test_returns_point_on_extended_line(self):
        point1 = Point('P1', 50, 50)
        point2 = Point('P2', 100, 100)

        point3 = get_point_on_line(point1, point2, distance=140, title='T1')
        self.assertAlmostEqual(point3.x, 148.99, delta=0.01)
        self.assertAlmostEqual(point3.y, 148.99, delta=0.01)

        elems = [
            point1.as_csv(), point2.as_csv(), point3.as_csv(),
            Path(point1, point3).as_csv()]
        return False, elems


class GetDomeInnerRadiusTest(TestCase):

    @debug_dump
    def test_returns_dome_radius(self):

        surface_circle_center_point = Point('SCCP', 800, 800)
        surface_inner_radius = 500

        dome_radius, dome_circle_center_point, first_row_outer_top_point = get_dome_inner_radius(
            surface_circle_center_point, surface_inner_radius)

        self.assertEqual(dome_radius, 671.3)
        self.assertEqual(get_distance(dome_circle_center_point, first_row_outer_top_point), 661.3)

        elems = [
            surface_circle_center_point.as_csv(),
            dome_circle_center_point.as_csv(),
            first_row_outer_top_point.as_csv(),
            Path(first_row_outer_top_point, dome_circle_center_point).as_csv()]
        return False, elems


class GetDegreeElementsTest(TestCase):

    @debug_dump
    def test_returns_angle_degree_between_top_and_bottom_surfaces(self):
        a_point = Point('A', 100, 130)
        b_point = Point('B', 180, 130)
        e_point = Point('E', 120, 230)
        f_point = Point('F', 160, 230)

        degree_elements = get_degree_elements(
            a_point, b_point, e_point, f_point,
            degree_x_offset=180)

        degree_element = degree_elements[-1]

        # Ensure the angle degree between top and bottom surfaces is correct.
        self.assertIn(u'>78.7°<', degree_element)
        elems = [
            a_point.as_csv(),
            b_point.as_csv(),
            e_point.as_csv(),
            f_point.as_csv()
        ]
        elems.extend(degree_elements)
        return False, elems


def dump_svg(inner_elems):
    scale = 3.78
    scale /= 2
    elems = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg version="1.1" width="2000mm" height="10000mm" xmlns="http://www.w3.org/2000/svg" >',
        '<g transform="scale({})">'.format(scale)
    ]
    elems.extend(inner_elems)

    with open('/tmp/domes_test1.svg', 'w') as f:
        elems.append('</g></svg>')
        total_layout = '\n'.join([str(x) for x in elems])
        f.write(total_layout)


if __name__ == '__main__':
    unittest_main()
