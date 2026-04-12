import board
import busio
import digitalio
import adafruit_sdcard
import storage # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error

from models.packet import Packet

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False # pyright: ignore[reportConstantRedefinition]

if TYPE_CHECKING:
    from typing import Optional

class PersistenceManager:

    def __init__(self, pcontrol_path: str, pdata_path: str) -> None:
        # self.__init_device__()
        pass
        
    def __init_device__(self):
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs = digitalio.DigitalInOut(board.A5)
        sdcard = adafruit_sdcard.SDCard(spi, cs)
        vfs = storage.VfsFat(sdcard) # pyright: ignore[reportArgumentType]
        storage.mount(vfs, "/sd")

    ## Add logging message implementation
    def log_packet(self, packet: Packet) -> None:
        raise NotImplementedError

    def retrieve_packet(self, identifier: int) -> "Optional[Packet]":
        raise NotImplementedError

