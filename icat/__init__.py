import shutil
import sys
from io import BytesIO
from os import getenv
from pathlib import Path
from subprocess import run
from typing import Optional

import matplotlib
from IPython.core.getipython import get_ipython
from IPython.core.magic import Magics, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import FigureManagerBase, _Backend
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image

if hasattr(sys, "ps1") or sys.flags.interactive:
    interactive(True)


def _run(*cmd):
    def f(*args, output=True, fit_to_terminal=False, img_width=None, img_height=None, **kwargs):
        # Build command with optional fit parameters
        cmd_args = list(args)
        
        if fit_to_terminal and img_width and img_height:
            # Calculate terminal-fit dimensions
            fit_width, fit_height = _get_fit_dimensions(img_width, img_height)
            # Use --place to specify cell dimensions for kitty
            cmd_args = [f"--place={fit_width}x{fit_height}@0x0"] + cmd_args
        
        if output:
            kwargs["capture_output"] = True
            kwargs["text"] = True
        r = run(cmd + tuple(cmd_args), **kwargs)
        if output:
            return r.stdout.rstrip()

    return f


_icat = _run("kitten", "icat", "--align", "left")


def _get_fit_dimensions(img_width: int, img_height: int) -> tuple[int, int]:
    """Calculate dimensions to fit image maximally in terminal.
    
    Args:
        img_width: Original image width in pixels
        img_height: Original image height in pixels
        
    Returns:
        Tuple of (width, height) in character cells that fit the terminal
    """
    try:
        term_size = shutil.get_terminal_size()
        term_cols = term_size.columns
        term_rows = term_size.lines
    except Exception:
        # Fallback to a reasonable default if terminal size can't be determined
        term_cols, term_rows = 80, 24
    
    # Leave margin for prompt and output (2 rows for prompt, 2 cols for spacing)
    max_rows = max(term_rows - 2, 1)
    max_cols = max(term_cols - 2, 1)
    
    # Calculate aspect ratio of the image
    img_aspect = img_width / img_height if img_height > 0 else 1.0
    
    # Terminal character cells are typically twice as tall as they are wide
    # So to preserve image aspect ratio, we need to account for this:
    # If image is W x H pixels, and we want it to look right in terminal,
    # we need (cols / 2) / rows = W / H
    # Therefore: cols = 2 * rows * (W / H)
    # And: rows = cols / (2 * (W / H))
    
    # Try fitting by width first
    rows_if_full_width = max_cols / (2 * img_aspect)
    
    if rows_if_full_width <= max_rows:
        # Image fits when using full width
        return max_cols, max(1, int(rows_if_full_width))
    else:
        # Image is too tall, constrain by height
        cols_if_full_height = 2 * max_rows * img_aspect
        
        if cols_if_full_height <= max_cols:
            # Fits within column constraint
            return max(1, int(cols_if_full_height)), max_rows
        else:
            # Still too wide even at max height, just use max dimensions
            # This shouldn't normally happen with reasonable images
            return max_cols, max_rows


class FigureManagerICat(FigureManagerBase):
    def show(self):
        with BytesIO() as buf:
            self.canvas.figure.savefig(buf, format="png")
            
            # Check if fit is enabled via environment variable
            fit_enabled = getenv("IPYTHON_ICAT_FIT", "").strip().lower() in {"1", "true", "yes", "on"}
            
            if fit_enabled:
                # Get image dimensions
                buf.seek(0)
                img = Image.open(buf)
                img_width, img_height = img.size
                img.close()  # Close to release buffer
                buf.seek(0)
                _icat(output=False, input=buf.getvalue(), fit_to_terminal=True, img_width=img_width, img_height=img_height)
            else:
                _icat(output=False, input=buf.getvalue())


class FigureCanvasICat(FigureCanvasAgg):
    manager_class = FigureManagerICat


@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = FigureCanvasICat
    FigureManager = FigureManagerICat
    mainloop = lambda: None

    @classmethod
    def draw_if_interactive(cls):
        manager = Gcf.get_active()
        if is_interactive() and manager.canvas.figure.get_axes():
            cls.show()

    @classmethod
    def show(cls, *args, **kwargs):
        _Backend.show(*args, **kwargs)
        Gcf.destroy_all()


@magics_class
class ICatMagics(Magics):
    @magic_arguments()
    @argument(
        "target",
        nargs="?",
        help="Toggle on/off/status, a Python expression that evaluates to a PIL Image, or a path to an image file",
    )
    @argument("-W", "--width", type=int, help="Width to resize the image")
    @argument("-H", "--height", type=int, help="Height to resize the image")
    @argument("-f", "--fit", action="store_true", help="Fit image to terminal size")
    @line_magic
    def icat(self, line):
        args = parse_argstring(self.icat, line)
        target = (args.target or "").strip()

        if target in {"", "on"}:
            _enable_session(self.shell)
            return
        if target == "off":
            _disable_session(self.shell)
            return
        if target == "status":
            _print_status(self.shell)
            return

        obj = _resolve_target(self.shell, target)
        if obj is None:
            print(
                f"Error: could not resolve '{target}' as an image expression or file path."
            )
            return

        img = _coerce_to_image(obj)
        if img is None:
            print(
                f"Error: '{target}' did not evaluate to a PIL Image or readable image path."
            )
            return

        # Check if fit is requested via flag or environment variable
        fit_enabled = args.fit or getenv("IPYTHON_ICAT_FIT", "").strip().lower() in {"1", "true", "yes", "on"}

        # resize the image if width or height is specified
        if args.width or args.height:
            img.thumbnail((args.width or img.width, args.height or img.height))

        # display image
        with BytesIO() as buf:
            img.save(buf, format="PNG")
            
            if fit_enabled and not (args.width or args.height):
                # Only apply fit if manual dimensions aren't specified
                img_width, img_height = img.size
                _icat(output=False, input=buf.getvalue(), fit_to_terminal=True, img_width=img_width, img_height=img_height)
            else:
                _icat(output=False, input=buf.getvalue())


def icat(img: Image.Image, width: Optional[int] = None, height: Optional[int] = None, fit: bool = False):
    """Display a PIL Image in the terminal.
    
    Args:
        img: PIL Image to display
        width: Optional width to resize to
        height: Optional height to resize to
        fit: If True, fit image to terminal size (ignored if width/height specified)
    """
    img_ = img.copy()
    
    # Check if fit is requested via parameter or environment variable
    fit_enabled = fit or getenv("IPYTHON_ICAT_FIT", "").strip().lower() in {"1", "true", "yes", "on"}
    
    with BytesIO() as buf:
        if width or height:
            img_.thumbnail((width or img.width, height or img.height))
        img_.save(buf, format="PNG")
        
        if fit_enabled and not (width or height):
            # Only apply fit if manual dimensions aren't specified
            img_width, img_height = img_.size
            _icat(output=False, input=buf.getvalue(), fit_to_terminal=True, img_width=img_width, img_height=img_height)
        else:
            _icat(output=False, input=buf.getvalue())


def load_ipython_extension(ipython):
    ipython.register_magics(ICatMagics)

    auto = getenv("IPYTHON_ICAT_AUTO", "").strip().lower()
    if auto in {"1", "true", "yes", "on"}:
        _enable_session(ipython)


def _session_state(shell) -> dict:
    return shell.user_ns.setdefault("_icat_state", {})


def _enable_session(shell) -> None:
    state = _session_state(shell)
    if state.get("enabled"):
        return

    try:
        state["prev_mpl_backend"] = matplotlib.get_backend()
    except Exception:
        state["prev_mpl_backend"] = None

    try:
        matplotlib.use("module://icat")
        print("icat: enabled matplotlib backend + PIL auto-render")
    except Exception as e:
        print(f"icat: failed to enable matplotlib backend: {e}")

    try:
        _enable_pil_autorender(shell)
    except Exception as e:
        print(f"icat: failed to enable PIL auto-render: {e}")

    state["enabled"] = True


def _disable_session(shell) -> None:
    state = _session_state(shell)
    if not state.get("enabled"):
        return

    try:
        _disable_pil_autorender(shell)
    except Exception as e:
        print(f"icat: failed to disable PIL auto-render: {e}")

    prev_backend = state.get("prev_mpl_backend")
    if prev_backend:
        try:
            matplotlib.use(prev_backend)
            print(f"icat: restored matplotlib backend to {prev_backend!r}")
        except Exception as e:
            print(f"icat: failed to restore matplotlib backend {prev_backend!r}: {e}")

    state.clear()


def _print_status(shell) -> None:
    state = _session_state(shell)
    enabled = bool(state.get("enabled"))
    prev = state.get("prev_mpl_backend")
    current = None
    try:
        current = matplotlib.get_backend()
    except Exception:
        pass
    print(
        f"icat: enabled={enabled}, matplotlib_backend={current!r}, prev_backend={prev!r}"
    )


def _resolve_target(shell, target: str):
    try:
        return shell.ev(target)
    except Exception:
        pass

    try:
        path = Path(target).expanduser()
        if path.is_file():
            return path
    except Exception:
        pass

    return None


def _coerce_to_image(obj):
    if isinstance(obj, Image.Image):
        return obj.copy()

    if isinstance(obj, (str, Path)):
        path = Path(obj).expanduser()
        if path.is_file():
            return Image.open(path)

    return None


def _enable_pil_autorender(shell) -> None:
    ip = get_ipython()
    if ip is None:
        ip = shell

    state = _session_state(shell)
    fmt = ip.display_formatter.formatters["text/plain"]

    if "_prev_pil_printer_present" not in state:
        state["_prev_pil_printer_present"] = Image.Image in fmt.type_printers
        state["_prev_pil_printer"] = fmt.type_printers.get(Image.Image)

    def _pil_printer(img, _pprinter, _cycle):
        icat(img)
        return f"<PIL.Image.Image size={img.size} mode={img.mode} (rendered by icat)>"

    fmt.for_type(Image.Image, _pil_printer)


def _disable_pil_autorender(shell) -> None:
    ip = get_ipython()
    if ip is None:
        ip = shell

    state = _session_state(shell)
    fmt = ip.display_formatter.formatters["text/plain"]

    prev_present = bool(state.get("_prev_pil_printer_present"))
    if not prev_present:
        fmt.type_printers.pop(Image.Image, None)
        return

    fmt.for_type(Image.Image, state.get("_prev_pil_printer"))
