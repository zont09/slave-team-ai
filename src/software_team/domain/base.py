from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Base class cho toàn bộ domain model của hệ thống."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )