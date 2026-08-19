from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Iterator


# ==========================================
# 1. DOMAIN MODELS & VALUE OBJECTS
# ==========================================

class Genre(Enum):
    POP = "POP"
    ROCK = "ROCK"
    EDM = "EDM"
    HIP_HOP = "HIP_HOP"
    JAZZ = "JAZZ"


class Song:
    """Immutable domain model representing a music track."""
    def __init__(self, song_id: str, title: str, artist: str, genre: Genre, bpm: int, is_explicit: bool):
        self._song_id: str = song_id
        self._title: str = title
        self._artist: str = artist
        self._genre: Genre = genre
        self._bpm: int = bpm
        self._is_explicit: bool = is_explicit

    @property
    def song_id(self) -> str: return self._song_id
    @property
    def title(self) -> str: return self._title
    @property
    def artist(self) -> str: return self._artist
    @property
    def genre(self) -> Genre: return self._genre
    @property
    def bpm(self) -> int: return self._bpm
    @property
    def is_explicit(self) -> bool: return self._is_explicit

    def __repr__(self) -> str:
        return f"Song('{self._title}' - {self._genre.value})"


class UserPreferences:
    """User preferences used for filtering tracks."""
    def __init__(self, allowed_genres: List[Genre], min_bpm: int, max_bpm: int, allow_explicit: bool):
        self.allowed_genres: List[Genre] = allowed_genres
        self.min_bpm: int = min_bpm
        self.max_bpm: int = max_bpm
        self.allow_explicit: bool = allow_explicit


# ==========================================
# 2. FILTERING LAYER (Chain of Responsibility)
# ==========================================

class SongFilter(ABC):
    """Abstract Strategy interface for applying user preferences filters."""
    @abstractmethod
    def satisfies(self, song: Song, prefs: UserPreferences) -> bool:
        pass


class GenreFilter(SongFilter):
    def satisfies(self, song: Song, prefs: UserPreferences) -> bool:
        if not prefs.allowed_genres:
            return True
        return song.genre in prefs.allowed_genres


class BpmFilter(SongFilter):
    def satisfies(self, song: Song, prefs: UserPreferences) -> bool:
        return prefs.min_bpm <= song.bpm <= prefs.max_bpm


class ExplicitContentFilter(SongFilter):
    def satisfies(self, song: Song, prefs: UserPreferences) -> bool:
        if not prefs.allow_explicit and song.is_explicit:
            return False
        return True


class FilterPipeline:
    """Composite pipeline that executes all active filters on candidate tracks."""
    def __init__(self):
        self._filters: List[SongFilter] = [
            GenreFilter(),
            BpmFilter(),
            ExplicitContentFilter()
        ]

    def is_allowed(self, song: Song, prefs: UserPreferences) -> bool:
        return all(f.satisfies(song, prefs) for f in self._filters)


# ==========================================
# 3. SERVICE ADAPTERS (Song Providers)
# ==========================================

class SongProvider(ABC):
    """Unified interface for stream providers."""
    @abstractmethod
    def fetch_next_valid_song(self, prefs: UserPreferences, pipeline: FilterPipeline) -> Optional[Song]:
        pass


class DJService(SongProvider):
    """Source stream 1: Curated DJ playlist provider."""
    def __init__(self, tracks: List[Song]):
        self._tracks: List[Song] = tracks
        self._cursor: int = 0

    def fetch_next_valid_song(self, prefs: UserPreferences, pipeline: FilterPipeline) -> Optional[Song]:
        while self._cursor < len(self._tracks):
            candidate = self._tracks[self._cursor]
            self._cursor += 1
            if pipeline.is_allowed(candidate, prefs):
                return candidate
        return None


class RecommendationService(SongProvider):
    """Source stream 2: ML-driven Recommendation engine provider."""
    def __init__(self, tracks: List[Song]):
        self._tracks: List[Song] = tracks
        self._cursor: int = 0

    def fetch_next_valid_song(self, prefs: UserPreferences, pipeline: FilterPipeline) -> Optional[Song]:
        while self._cursor < len(self._tracks):
            candidate = self._tracks[self._cursor]
            self._cursor += 1
            if pipeline.is_allowed(candidate, prefs):
                return candidate
        return None


# ==========================================
# 4. MIXING STRATEGY (Strategy Pattern)
# ==========================================

class ProportionRatio:
    """Value object defining the mixing ratio (e.g., 2 DJ songs : 1 Rec song)."""
    def __init__(self, dj_count: int, rec_count: int):
        if dj_count < 0 or rec_count < 0 or (dj_count == 0 and rec_count == 0):
            raise ValueError("Invalid ratio allocation.")
        self.dj_count: int = dj_count
        self.rec_count: int = rec_count


class MixStrategy(ABC):
    """Strategy interface for blending tracks from multiple providers."""
    @abstractmethod
    def mix(
        self, 
        dj_service: SongProvider, 
        rec_service: SongProvider, 
        target_count: int, 
        prefs: UserPreferences, 
        pipeline: FilterPipeline
    ) -> List[Song]:
        pass


class ProportionMixStrategy(MixStrategy):
    """Handles both Equal (1:1) and Custom Proportion (N:M) mixing logic seamlessly."""
    def __init__(self, ratio: ProportionRatio):
        self._ratio: ProportionRatio = ratio

    def mix(
        self, 
        dj_service: SongProvider, 
        rec_service: SongProvider, 
        target_count: int, 
        prefs: UserPreferences, 
        pipeline: FilterPipeline
    ) -> List[Song]:
        mixed_playlist: List[Song] = []
        
        while len(mixed_playlist) < target_count:
            added_in_round = 0
            
            # 1. Pull N songs from DJ Service
            for _ in range(self._ratio.dj_count):
                if len(mixed_playlist) >= target_count:
                    break
                song = dj_service.fetch_next_valid_song(prefs, pipeline)
                if song:
                    mixed_playlist.append(song)
                    added_in_round += 1

            # 2. Pull M songs from Recommendation Service
            for _ in range(self._ratio.rec_count):
                if len(mixed_playlist) >= target_count:
                    break
                song = rec_service.fetch_next_valid_song(prefs, pipeline)
                if song:
                    mixed_playlist.append(song)
                    added_in_round += 1

            # Fallback Guard: Exit if both services run out of matching tracks
            if added_in_round == 0:
                break

        return mixed_playlist


# ==========================================
# 5. ORCHESTRATOR HUB (Playlist Engine)
# ==========================================

class PlaylistMixerEngine:
    """Main OrchestratorFacade managing playlist compilation requests."""
    def __init__(self, dj_service: SongProvider, rec_service: SongProvider):
        self._dj_service: SongProvider = dj_service
        self._rec_service: SongProvider = rec_service
        self._filter_pipeline: FilterPipeline = FilterPipeline()

    def generate_playlist(
        self, 
        strategy: MixStrategy, 
        target_count: int, 
        user_prefs: UserPreferences
    ) -> List[Song]:
        return strategy.mix(
            dj_service=self._dj_service,
            rec_service=self._rec_service,
            target_count=target_count,
            prefs=user_prefs,
            pipeline=self._filter_pipeline
        )


# ==========================================
# 6. RUNTIME DEMONSTRATION
# ==========================================

if __name__ == "__main__":
    # Mock Data Sets
    dj_tracks = [
        Song("1", "EDM Bang 1", "DJ Snake", Genre.EDM, 128, False),
        Song("2", "Heavy Rock", "AC/DC", Genre.ROCK, 140, True),     # Filtered out if no explicit
        Song("3", "EDM Bang 2", "Avicii", Genre.EDM, 126, False),
        Song("4", "Chill Jazz", "Miles D", Genre.JAZZ, 90, False),  # Filtered out if low BPM
    ]

    rec_tracks = [
        Song("10", "Pop Hit 1", "Dua Lipa", Genre.POP, 120, False),
        Song("11", "EDM Anthem", "Zedd", Genre.EDM, 128, False),
        Song("12", "Pop Hit 2", "Taylor S", Genre.POP, 118, False),
    ]

    # Initialize Services
    dj_service = DJService(dj_tracks)
    rec_service = RecommendationService(rec_tracks)
    engine = PlaylistMixerEngine(dj_service, rec_service)

    # Configure Preferences (Min BPM 110, Only POP/EDM/ROCK, No Explicit)
    prefs = UserPreferences(
        allowed_genres=[Genre.EDM, Genre.POP, Genre.ROCK],
        min_bpm=110,
        max_bpm=150,
        allow_explicit=False
    )

    # Blend with Custom Proportion: 2 DJ Songs for every 1 Recommendation Song (2:1 Ratio)
    custom_ratio = ProportionRatio(dj_count=2, rec_count=1)
    mixer_strategy = ProportionMixStrategy(ratio=custom_ratio)

    playlist = engine.generate_playlist(
        strategy=mixer_strategy, 
        target_count=5, 
        user_prefs=prefs
    )

    print("--- Final Generated Playlist Stream ---")
    for idx, song in enumerate(playlist, 1):
        print(f"{idx}. {song.title} | Genre: {song.genre.value} | BPM: {song.bpm}")