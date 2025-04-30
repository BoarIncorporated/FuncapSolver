class FuncaptchaError(Exception):
    """Base exception for all Funcaptcha-related errors."""

    pass


class PresetNotFoundError(FuncaptchaError):
    """Raised when a preset cannot be found."""

    pass


class ChallengeDataError(FuncaptchaError):
    """Raised when the challenge data is invalid or cannot be retrieved."""

    pass


class TooManyWavesError(FuncaptchaError):
    """Raised when the challenge exceeds the maximum allowed waves."""

    pass


class MissingAnswersError(FuncaptchaError):
    """Raised when not all expected answers are provided for the challenge."""

    pass


class PredictionError(FuncaptchaError):
    """Raised when the image prediction endpoint returns an error or invalid response."""

    pass
