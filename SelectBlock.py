import sublime  # pylint: disable=import-error
import sublime_plugin  # pylint: disable=import-error

def str_indentation(s):
    return len(s) - len(s.lstrip(' '))

def line_str_by_row(view, r):
    return view.substr(view.line(view.text_point(r, 0)))

def line_is_empty(s):
    return (not s) or s.isspace()

def line_is_top_level(s):
    return str_indentation(s) < 1

def line_is_nonempty_top_level(s):
    return not line_is_empty(s) and line_is_top_level(s)

def last_row(view):
    (row, _) = view.rowcol(view.size())
    return row

def pan_up_to_top_level(view, begin_point):
    (begin_row, _) = view.rowcol(begin_point)
    begin_line_str = view.substr(view.line(begin_point))

    just_seen_top_level = line_is_nonempty_top_level(begin_line_str)

    consider_row = begin_row - 1

    while True:
        # Stop at the first row.
        if consider_row < 1:
            return 0

        consider_line_str = line_str_by_row(view, consider_row)

        # Stop at an empty line after seeing a top-level declaration.
        if just_seen_top_level and line_is_empty(consider_line_str):
            return consider_row + 1

        just_seen_top_level = line_is_nonempty_top_level(consider_line_str)
        consider_row -= 1
        continue

def pan_down_to_top_level(view, begin_point):
    (begin_row, _) = view.rowcol(begin_point)
    begin_line_str = view.substr(view.line(begin_point))

    # Switch behaviour if the selected line is itself at the top level.
    taking_top_level = line_is_nonempty_top_level(begin_line_str)

    consider_row = begin_row + 1
    pan_last_row = last_row(view)

    while True:
        # Stop at the last row.
        if consider_row >= pan_last_row:
            return pan_last_row

        consider_line_str = line_str_by_row(view, consider_row)

        # If starting at the top level, add rows until seeing an empty line,
        # at which point resume normal behaviour of adding until the next
        # top-level declaration.
        if taking_top_level:
            # Continue taking lines until we see an empty line.
            taking_top_level = not line_is_empty(consider_line_str)
            consider_row += 1
            continue
        # In normal behaviour, stop at the next top-level declaration.
        if line_is_nonempty_top_level(consider_line_str):
            return consider_row

        consider_row += 1
        continue

def expand_region(view, region):
    begin_point = region.begin()
    result_begin_row = pan_up_to_top_level(view, begin_point)

    end_point = region.end()
    result_end_row = pan_down_to_top_level(view, end_point)

    return sublime.Region(view.text_point(result_begin_row, 0),
                          view.text_point(result_end_row, 0))

class SelectBlockCommand(sublime_plugin.TextCommand):  # pylint: disable=too-few-public-methods
    def run(self, _edit):
        selection = self.view.sel()
        new_regions = list(map(lambda r: expand_region(self.view, r), selection))
        selection.clear()
        selection.add_all(new_regions)
