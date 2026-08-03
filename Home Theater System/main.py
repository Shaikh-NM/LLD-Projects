class TheaterLights:
    def dim(self, level: int) -> None:
        pass

    def on(self) -> None:
        pass

class Projector:
    def turn_on(self) -> None:
        print(f"Projector turned on successfully")

    def set_input(self, source: str) -> None:
        pass

    def wide_screen_mode(self) -> None:
        pass

class Amplifier:
    pass

class StreamingPlayer:
    pass

class PopcornPopper:
    pass

from abc import ABC, abstractmethod
class TheaterStartupTemplate(ABC):
    def __init__(self, lights: TheaterLights, projector: Projector, amplifier: Amplifier, player: StreamingPlayer):
        self._lights: TheaterLights = lights
        self._projector: Projector = projector
        self._amp: Amplifier = amplifier
        self._player: StreamingPlayer = player

    def execute_startup_sequence(self, movie_title: str)->None:
        self._prepare_environment()
        self._configure_display()
        self._configure_audio()
        self._start_media(movie_title)

    def _start_media(self, movie_title: str):
        self._player.turn_on()
        self.player.play_movie(movie_title)

    @abstractmethod
    def _prepare_environment(self)->None:
        pass

    @abstractmethod
    def _configure_display(self)->None:
        pass

    @abstractmethod
    def _configure_display(self)->None:
        pass

class CinemaProfile(TheaterStartupTemplate):
    def __init__(self, lights: TheaterLights, projector: Projector, amp: Amplifier, player: StreamingPlayer, popper: PopcornPopper):
        super().__init__(lights, projector, amp, player)
        self._popper: PopcornPopper = popper

    def _prepare_environment(self)->None:
        self._popper.turn_on()
        self._popper.pop()
        self._lights.dim(level=10)

    def _configure_display(self)->None:
        self._projector.turn_on()
        self._projector.set_input("Streaming Box")
        self._projector.wide_screen_mode()

    def _configure_audio(self)->None:
        self._amp.turn_on()
        self._amp.set_surround_sound("Dolby Atmos 7.1")
        self._amp.set_volume(level=75)

class NightModeProfile(TheaterStartupTemplate):
    print("NightModeProfile") # remove this later

class HomeTheaterFacade:
    def __init__(self, startup_profile: TheaterStartupTemplate):
        self._startup_template: TheaterStartupTemplate = startup_profile

    def set_profile(self, profile: TheaterStartupTemplate)->None:
        self._startup_profile = profile

    def watch_movie(self, movie_title: str)->None:
        self._startup_profile.execute_startup_sequence(movie_title=movie_title)
     
    




    


