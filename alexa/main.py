from abc import ABC, abstractmethod

# ==========================================
# 1. POWER SOURCE SUBSYSTEM (Bridge Interface)
# ==========================================

class PowerSource(ABC):
    """Abstract interface defining power and battery behaviors."""

    def __init__(self, is_charging: bool = False):
        self._is_charging: bool = is_charging

    @property
    def is_charging(self) -> bool:
        return self._is_charging

    def plug_in(self) -> None:
        self._is_charging = True

    def unplug(self) -> None:
        self._is_charging = False

    @abstractmethod
    def get_battery_status(self) -> str:
        """Returns the formatted battery and charging status string."""
        pass


class BatteryPowerSource(PowerSource):
    """Concrete implementation for devices equipped with an internal battery."""

    def __init__(self, initial_percentage: int, is_charging: bool = False):
        super().__init__(is_charging)
        self._percentage: int = max(0, min(100, initial_percentage))

    @property
    def percentage(self) -> int:
        return self._percentage

    @percentage.setter
    def percentage(self, value: int) -> None:
        self._percentage = max(0, min(100, value))

    def get_battery_status(self) -> str:
        charging_prefix = "Charging" if self._is_charging else "Not charging"
        return f"{charging_prefix}, Battery: {self._percentage}%"


class DirectACPowerSource(PowerSource):
    """Concrete implementation for devices without an internal battery (wall-plugged only)."""

    def __init__(self, is_charging: bool = False):
        super().__init__(is_charging)

    def get_battery_status(self) -> str:
        charging_prefix = "Charging" if self._is_charging else "Not charging"
        return f"{charging_prefix}, Battery not available"


# ==========================================
# 2. DEVICE HIERARCHY (Device Abstractions)
# ==========================================

class AlexaDevice(ABC):
    """Base device abstraction holding a reference to its PowerSource."""

    def __init__(self, name: str, power_source: PowerSource):
        self._name: str = name
        self._power_source: PowerSource = power_source

    @property
    def name(self) -> str:
        return self._name

    def plug_in(self) -> None:
        self._power_source.plug_in()

    def unplug(self) -> None:
        self._power_source.unplug()

    def show(self) -> None:
        """Displays the device name alongside its battery and charging status."""
        status = self._power_source.get_battery_status()
        print(f"[{self._name}] -> {status}")


class AudioOnlyDevice(AlexaDevice):
    """e.g., Echo Dot / Echo Pop"""
    def play_sound(self, audio: str) -> None:
        print(f"🔊 [{self.name}] Playing: '{audio}'")


class ScreenOnlyDevice(AlexaDevice):
    """e.g., Smart Digital Frame / Display Stand"""
    def render_display(self, content: str) -> None:
        print(f"🖥️ [{self.name}] Displaying: '{content}'")


class AudioAndScreenDevice(AlexaDevice):
    """e.g., Echo Show / Echo Spot"""
    def play_multimedia(self, media_title: str) -> None:
        print(f"🔊🖥️ [{self.name}] Streaming Video & Audio: '{media_title}'")


# ==========================================
# 3. RUNTIME DEMONSTRATION OF ALL 4 STATES
# ==========================================

if __name__ == "__main__":
    print("=== DEMONSTRATING THE 4 BATTERY & CHARGING STATES ===\n")

    portable_dot = AudioOnlyDevice(
        name="Echo Dot Portable",
        power_source=BatteryPowerSource(initial_percentage=85, is_charging=True)
    )
    portable_dot.show()

    wall_echo_show = AudioAndScreenDevice(
        name="Echo Show 10 (Wall Unit)",
        power_source=DirectACPowerSource(is_charging=True)
    )
    wall_echo_show.show()

    portable_speaker = AudioOnlyDevice(
        name="Echo Tap (Outdoor)",
        power_source=BatteryPowerSource(initial_percentage=42, is_charging=False)
    )
    portable_speaker.show()

    smart_frame = ScreenOnlyDevice(
        name="Echo Smart Screen",
        power_source=DirectACPowerSource(is_charging=False)
    )
    smart_frame.show()