from abc import ABC
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

from ..generic import ArrayObject, DictionaryObject
from ..generic._base import (
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)
from ..generic._fit import DEFAULT_FIT, Fit
from ..generic._rectangle import RectangleObject
from ..generic._utils import hex_to_rgb
from ._base import AnnotationDictionary

try:
    from typing import TypeAlias  # type: ignore[attr-defined]
except ImportError:
    # PEP 613 introduced typing.TypeAlias with Python 3.10
    # For older Python versions, the backport typing_extensions is necessary:
    from typing_extensions import TypeAlias  # type: ignore[misc]


Vertex: TypeAlias = Tuple[float, float]


def _get_bounding_rectangle(vertices: List[Vertex]) -> RectangleObject:
    x_min, y_min = vertices[0][0], vertices[0][1]
    x_max, y_max = vertices[0][0], vertices[0][1]
    for x, y in vertices:
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x)  ## !!! error? : min -> max
        y_max = max(y_max, y)  ## !!! error? : min -> max
    rect = RectangleObject((x_min, y_min, x_max, y_max))
    return rect


class MarkupAnnotation(AnnotationDictionary, ABC):
    """
    Base class for all markup annotations.

    Args:
        title_bar: Text to be displayed in the title bar of the annotation;
            by convention this is the name of the author
    """

    def __init__(
        self,
        *,
        title_bar: Optional[str] = None,
        call_post_init: bool = False,
        **kwargs: Any,
    ):
        super().__init__()
        if title_bar is not None:
            self.title_bar = title_bar
        self = super().__init__()
        if call_post_init:
            self._post_init(**kwargs)

    @property
    def title_bar(self) -> str:
        return self.get("/T", "")

    @title_bar.setter
    def title_bar(self, value: Optional[str]) -> AnnotationDictionary:
        self._set_str("/T", value)
        return self


class Text(MarkupAnnotation):
    """
    A text annotation.

    Args:
        rect: array of four integers ``[xLL, yLL, xUR, yUR]``
            specifying the clickable rectangular area
        text: The text that is added to the document
        open:
        flags:
    """

    def __init__(
        self,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        text: str,
        *,
        open: bool = False,
        #### !!!! for me by default no Flags as it is optional
        #### int = NO_FLAGS,
        **kwargs: Any,
    ):
        super().__init__()
        self._set_name("/SubType", "/Text")
        self._set_name("/Rect", rect)
        self._set_str("/Contents", text)
        kwargs["open"] = open
        self._post_init(**kwargs)

    @property
    def open(self) -> bool:
        return self.get("/Open", False)

    @open.setter
    def open(self, value: Optional[bool]) -> AnnotationDictionary:
        self._set_bool("/Open", value)
        return self


class FreeText(MarkupAnnotation):
    """A FreeText annotation"""

    def __init__(
        self,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        text: str,
        *,
        font: str = "Helvetica",
        bold: bool = False,
        italic: bool = False,
        font_size: str = "14pt",
        font_color: str = "000000",
        border_color: Optional[str] = "000000",
        background_color: Optional[str] = "ffffff",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self[NameObject("/Subtype")] = NameObject("/FreeText")
        self[NameObject("/Rect")] = RectangleObject(rect)

        font_str = "font: "
        if bold is True:
            font_str = f"{font_str}bold "
        if italic is True:
            font_str = f"{font_str}italic "
        font_str = f"{font_str}{font} {font_size}"
        font_str = f"{font_str};text-align:left;color:#{font_color}"

        default_appearance_string = ""
        if border_color:
            for st in hex_to_rgb(border_color):
                default_appearance_string = f"{default_appearance_string}{st} "
            default_appearance_string = f"{default_appearance_string}rg"

        self.update(
            {
                NameObject("/Subtype"): NameObject("/FreeText"),
                NameObject("/Rect"): RectangleObject(rect),
                NameObject("/Contents"): TextStringObject(text),
                # font size color
                NameObject("/DS"): TextStringObject(font_str),
                NameObject("/DA"): TextStringObject(default_appearance_string),
            }
        )
        if border_color is None:
            # Border Style
            self[NameObject("/BS")] = DictionaryObject(
                {
                    # width of 0 means no border
                    NameObject("/W"): NumberObject(0)
                }
            )
        if background_color is not None:
            self[NameObject("/C")] = ArrayObject(
                [FloatObject(n) for n in hex_to_rgb(background_color)]
            )


class Line(MarkupAnnotation):
    def __init__(
        self,
        p1: Vertex,
        p2: Vertex,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        text: str = "",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.update(
            {
                NameObject("/Subtype"): NameObject("/Line"),
                NameObject("/Rect"): RectangleObject(rect),
                NameObject("/L"): ArrayObject(
                    [
                        FloatObject(p1[0]),
                        FloatObject(p1[1]),
                        FloatObject(p2[0]),
                        FloatObject(p2[1]),
                    ]
                ),
                NameObject("/LE"): ArrayObject(
                    [
                        NameObject(None),
                        NameObject(None),
                    ]
                ),
                NameObject("/IC"): ArrayObject(
                    [
                        FloatObject(0.5),
                        FloatObject(0.5),
                        FloatObject(0.5),
                    ]
                ),
                NameObject("/Contents"): TextStringObject(text),
            }
        )


class PolyLine(MarkupAnnotation):
    def __init__(
        self,
        vertices: List[Vertex],
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if len(vertices) == 0:
            raise ValueError("A polygon needs at least 1 vertex with two coordinates")
        coord_list = []
        for x, y in vertices:
            coord_list.append(NumberObject(x))
            coord_list.append(NumberObject(y))
        self.update(
            {
                NameObject("/Subtype"): NameObject("/PolyLine"),
                NameObject("/Vertices"): ArrayObject(coord_list),
                NameObject("/Rect"): RectangleObject(_get_bounding_rectangle(vertices)),
            }
        )


class Rectangle(MarkupAnnotation):
    def __init__(
        self,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        *,
        interiour_color: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.update(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Square"),
                NameObject("/Rect"): RectangleObject(rect),
            }
        )

        if interiour_color:
            self[NameObject("/IC")] = ArrayObject(
                [FloatObject(n) for n in hex_to_rgb(interiour_color)]
            )


class Highlight(MarkupAnnotation):
    def __init__(
        self,
        *,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        quad_points: ArrayObject,
        highlight_color: str = "ff0000",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.update(
            {
                NameObject("/Subtype"): NameObject("/Highlight"),
                NameObject("/Rect"): RectangleObject(rect),
                NameObject("/QuadPoints"): quad_points,
                NameObject("/C"): ArrayObject(
                    [FloatObject(n) for n in hex_to_rgb(highlight_color)]
                ),
            }
        )


class Ellipse(MarkupAnnotation):
    def __init__(
        self,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        *,
        interiour_color: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.update(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Circle"),
                NameObject("/Rect"): RectangleObject(rect),
            }
        )

        if interiour_color:
            self[NameObject("/IC")] = ArrayObject(
                [FloatObject(n) for n in hex_to_rgb(interiour_color)]
            )


class Polygon(MarkupAnnotation):
    def __init__(
        self,
        vertices: List[Tuple[float, float]],
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if len(vertices) == 0:
            raise ValueError("A polygon needs at least 1 vertex with two coordinates")

        coord_list = []
        for x, y in vertices:
            coord_list.append(NumberObject(x))
            coord_list.append(NumberObject(y))
        self.update(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Polygon"),
                NameObject("/Vertices"): ArrayObject(coord_list),
                NameObject("/IT"): NameObject("PolygonCloud"),
                NameObject("/Rect"): RectangleObject(_get_bounding_rectangle(vertices)),
            }
        )


class Link(MarkupAnnotation):
    def __init__(
        self,
        *,
        rect: Union[RectangleObject, Tuple[float, float, float, float]],
        border: Optional[ArrayObject] = None,
        url: Optional[str] = None,
        target_page_index: Optional[int] = None,
        fit: Fit = DEFAULT_FIT,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if TYPE_CHECKING:
            from ..types import BorderArrayType

        is_external = url is not None
        is_internal = target_page_index is not None
        if not is_external and not is_internal:
            raise ValueError(
                "Either 'url' or 'target_page_index' have to be provided. Both were None."
            )
        if is_external and is_internal:
            raise ValueError(
                "Either 'url' or 'target_page_index' have to be provided. "
                f"url={url}, target_page_index={target_page_index}"
            )

        border_arr: BorderArrayType
        if border is not None:
            border_arr = [NameObject(n) for n in border[:3]]
            if len(border) == 4:
                dash_pattern = ArrayObject([NameObject(n) for n in border[3]])
                border_arr.append(dash_pattern)
        else:
            border_arr = [NumberObject(0)] * 3

        link_obj = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): RectangleObject(rect),
                NameObject("/Border"): ArrayObject(border_arr),
            }
        )
        if is_external:
            link_obj[NameObject("/A")] = DictionaryObject(
                {
                    NameObject("/S"): NameObject("/URI"),
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/URI"): TextStringObject(url),
                }
            )
        if is_internal:
            # This needs to be updated later!
            dest_deferred = DictionaryObject(
                {
                    "target_page_index": NumberObject(target_page_index),
                    "fit": NameObject(fit.fit_type),
                    "fit_args": fit.fit_args,
                }
            )
            link_obj[NameObject("/Dest")] = dest_deferred
