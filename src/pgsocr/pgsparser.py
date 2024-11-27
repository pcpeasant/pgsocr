from collections import namedtuple
from functools import cached_property
from dataclasses import dataclass
import warnings
from enum import Enum
import os.path
from PIL import Image


warnings.simplefilter("always", RuntimeWarning)


class InvalidSegmentError(Exception):
    pass


class SEGMENT_TYPE(Enum):
    PDS = 0x14
    ODS = 0x15
    PCS = 0x16
    WDS = 0x17
    END = 0x80


class BaseSegment:

    def __init__(self, raw_bytes: bytes):
        if raw_bytes[:2] != b"PG":
            raise InvalidSegmentError
        self.pts: int = int.from_bytes(raw_bytes[2:6], byteorder="big") // 90
        self.dts: int = int.from_bytes(raw_bytes[6:10], byteorder="big") // 90
        self.type: SEGMENT_TYPE = SEGMENT_TYPE(raw_bytes[10])
        self.size: int = int.from_bytes(raw_bytes[11:13], byteorder="big")
        self.payload: bytes = raw_bytes[13:]

    def __len__(self):
        return self.size

    @property
    def segment_type(self) -> SEGMENT_TYPE:
        return self.type

    @property
    def presentation_timestamp(self) -> int:
        return self.pts


PaletteEntry = namedtuple("PaletteEntry", ["Y", "Cb", "Cr", "Alpha"])


class PaletteDefinitionSegment(BaseSegment):
    def __init__(self, raw_bytes: bytes):
        super().__init__(raw_bytes)
        self.id: int = self.payload[0]
        self.version: int = self.payload[1]
        # Multiple palette entries, iterate and store all
        self.palette = [PaletteEntry(0, 0, 0, 0)] * 256
        for entry in range(len(self.payload[2:]) // 5):
            i = 2 + entry * 5
            self.palette[self.payload[i]] = PaletteEntry(*self.payload[i + 1 : i + 5])


class ObjectDefinitionSegment(BaseSegment):
    SEQUENCE = {0x40: "Last", 0x80: "First", 0xC0: "First and last"}

    def __init__(self, raw_bytes: bytes):
        super().__init__(raw_bytes)
        self.id: int = int.from_bytes(self.payload[0:2], byteorder="big")
        self.version: int = self.payload[2]
        self.is_first: bool = bool(self.payload[3] & 0x80)
        self.is_last: bool = bool(self.payload[3] & 0x40)
        # Image data can be fragmented across multiple ODS
        # Data length, height, width properties only present in first ODS in a sequence
        if not self.is_first:
            self.img_data: bytes = self.payload[4:]
        else:
            self.data_len: int = int.from_bytes(self.payload[4:7], byteorder="big")
            self.width: int = int.from_bytes(self.payload[7:9], byteorder="big")
            self.height: int = int.from_bytes(self.payload[9:11], byteorder="big")
            self.img_data: bytes = self.payload[11:]


# Helper function to join ODS segments as described above
def make_ods(ods_list: list[ObjectDefinitionSegment]) -> ObjectDefinitionSegment:
    if len(ods_list) == 1:
        return ods_list[0]
    ret = ods_list[0]
    for ods in ods_list[1:]:
        ret.img_data += ods.img_data
    if len(ret.img_data) != ret.data_len - 4:
        warnings.warn(
            "Image data length from header does not match the length found.",
            RuntimeWarning,
            stacklevel=2,
        )
    ret.is_first = True
    ret.is_last = True
    return ret


class COMPOSITION_STATE(Enum):
    NORMAL = 0x00
    ACQUISITION_POINT = 0x40
    EPOCH_START = 0x80


class CompositionObject:
    def __init__(self, raw_bytes: bytes):
        self.object_id: int = int.from_bytes(raw_bytes[0:2], byteorder="big")
        self.window_id: int = raw_bytes[2]
        self.is_cropped: bool = bool(raw_bytes[3] & 0x80)
        self.is_forced: bool = bool(raw_bytes[3] & 0x40)
        self.x_pos: int = int.from_bytes(raw_bytes[4:6], byteorder="big")
        self.y_pos: int = int.from_bytes(raw_bytes[6:8], byteorder="big")
        if self.is_cropped:
            self.crop_x_offset: int = int.from_bytes(raw_bytes[8:10], byteorder="big")
            self.crop_y_offset: int = int.from_bytes(raw_bytes[10:12], byteorder="big")
            self.crop_width: int = int.from_bytes(raw_bytes[12:14], byteorder="big")
            self.crop_height: int = int.from_bytes(raw_bytes[14:16], byteorder="big")


class PresentationCompositionSegment(BaseSegment):
    def __init__(self, raw_bytes: bytes):
        super().__init__(raw_bytes)
        self.width: int = int.from_bytes(self.payload[0:2], byteorder="big")
        self.height: int = int.from_bytes(self.payload[2:4], byteorder="big")
        self.frame_rate: int = self.payload[4]
        self.num: int = int.from_bytes(self.payload[5:7], byteorder="big")
        self.state: COMPOSITION_STATE = COMPOSITION_STATE(self.payload[7])
        self.palette_update: bool = bool(self.payload[8])
        self.palette_id: int = self.payload[9]
        self.num_comp_objs: int = self.payload[10]

    @property
    def composition_number(self) -> int:
        return self.num

    @property
    def composition_state(self) -> COMPOSITION_STATE:
        return self.state

    @cached_property
    def composition_objects(self) -> list[CompositionObject]:
        idx = 11
        comps = []
        while idx < len(self.payload):
            length = 8 * (1 + bool(self.payload[idx + 3]))
            comps.append(CompositionObject(self.payload[idx : idx + length]))
            idx += length
        if len(comps) != self.num_comp_objs:
            warnings.warn(
                "Number of composition objects asserted does not match the amount found.",
                RuntimeWarning,
                stacklevel=2,
            )
        return comps


class WindowObject:
    def __init__(self, raw_bytes: bytes):
        self.id: int = raw_bytes[0]
        self.x_pos: int = int.from_bytes(raw_bytes[1:3], byteorder="big")
        self.y_pos: int = int.from_bytes(raw_bytes[3:5], byteorder="big")
        self.width: int = int.from_bytes(raw_bytes[5:7], byteorder="big")
        self.height: int = int.from_bytes(raw_bytes[7:9], byteorder="big")


class WindowDefinitionSegment(BaseSegment):
    def __init__(self, raw_bytes: bytes):
        super().__init__(raw_bytes)
        self.num_win_objs: int = self.payload[0]

    @cached_property
    def window_objects(self) -> list[WindowObject]:
        idx = 1
        windows = []
        while idx < len(self.payload):
            length = 9
            windows.append(WindowObject(self.payload[idx : idx + length]))
            idx += length
        if len(windows) != self.num_win_objs:
            warnings.warn(
                "Number of window objects asserted does not match the amount found.",
                RuntimeWarning,
                stacklevel=2,
            )
        return windows


class EndOfDisplaySetSegment(BaseSegment):
    pass


class DisplaySet:
    def __init__(self, segment_list: list[BaseSegment]):
        self.segments: list[BaseSegment] = segment_list
        self.segment_types: list[SEGMENT_TYPE] = [s.segment_type for s in segment_list]
        self.has_image: bool = SEGMENT_TYPE.ODS in self.segment_types

    @property
    def pcs(self) -> list[PresentationCompositionSegment]:
        return [
            s for s in self.segments if isinstance(s, PresentationCompositionSegment)
        ]

    @property
    def wds(self) -> list[WindowDefinitionSegment]:
        return [s for s in self.segments if isinstance(s, WindowDefinitionSegment)]

    @property
    def pds(self) -> list[PaletteDefinitionSegment]:
        return [s for s in self.segments if isinstance(s, PaletteDefinitionSegment)]

    @property
    def ods(self) -> list[ObjectDefinitionSegment]:
        return [s for s in self.segments if isinstance(s, ObjectDefinitionSegment)]

    @property
    def composition_state(self) -> COMPOSITION_STATE:
        return self.pcs[0].composition_state


class Epoch:
    def __init__(self, displayset_list: list[DisplaySet]):
        self.display_sets: list[DisplaySet] = displayset_list
        self.ds_states: list[COMPOSITION_STATE] = [
            ds.pcs[0].composition_state for ds in displayset_list
        ]


class PGStream:
    TYPE_TO_CLASS = {
        SEGMENT_TYPE.PDS: PaletteDefinitionSegment,
        SEGMENT_TYPE.ODS: ObjectDefinitionSegment,
        SEGMENT_TYPE.PCS: PresentationCompositionSegment,
        SEGMENT_TYPE.WDS: WindowDefinitionSegment,
        SEGMENT_TYPE.END: EndOfDisplaySetSegment,
    }

    def __init__(self, filepath: str):
        ext = os.path.splitext(filepath)[1]
        if ext != ".sup":
            raise ValueError(f"File with extension '{ext}' is not a valid SUP.")
        self.file_name: str = os.path.split(filepath)[1]
        with open(filepath, "rb") as f:
            self.raw_data: bytes = f.read()
        self.res_height = self.display_sets[0].pcs[0].height
        self.res_width = self.display_sets[0].pcs[0].width

    @cached_property
    def segments(self) -> list[BaseSegment]:
        idx = 0
        segs = []
        ods_list = []
        while idx < len(self.raw_data):
            size = 13 + int.from_bytes(
                self.raw_data[idx + 11 : idx + 13], byteorder="big"
            )
            seg_type = SEGMENT_TYPE(self.raw_data[idx + 10])
            cls = self.TYPE_TO_CLASS[seg_type]
            seg_instance = cls(self.raw_data[idx : idx + size])
            idx += size
            # ODS need to be handled separately in case of fragmented sequence
            if seg_type == SEGMENT_TYPE.ODS:
                ods_list.append(seg_instance)
                if seg_instance.is_last:
                    seg_instance = make_ods(ods_list)
                    ods_list = []
                else:
                    continue
            segs.append(seg_instance)
        return segs

    @cached_property
    def display_sets(self) -> list[DisplaySet]:
        ds = []
        cur = []
        for s in self.segments:
            cur.append(s)
            if s.type == SEGMENT_TYPE.END:
                ds.append(DisplaySet(cur))
                cur = []

        return sorted(ds, key=lambda x: x.pcs[0].presentation_timestamp)

    @cached_property
    def epochs(self) -> list[Epoch]:
        ep = []
        cur = []
        for ds in self.display_sets:
            if ds.pcs[0].composition_state == COMPOSITION_STATE.EPOCH_START:
                if cur:
                    ep.append(Epoch(cur))
                cur = []
            cur.append(ds)
        ep.append(Epoch(cur))
        return ep


@dataclass
class PGSImageObject:
    img: Image.Image
    x_pos: int
    y_pos: int
    start_ms: int
    end_ms: int
    pal: list[PaletteEntry]
