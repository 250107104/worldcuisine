"""Validation shared by the API's request models and route parameters."""
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints, model_validator


def _check_text(value: str) -> str:
    if "\x00" in value:
        raise ValueError("Text cannot contain a null character")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("Text must be valid UTF-8") from exc
    return value


InputText = Annotated[str, AfterValidator(_check_text)]
TrimmedText = Annotated[InputText, StringConstraints(strip_whitespace=True)]
BodyId = Annotated[TrimmedText, StringConstraints(min_length=1)]


class RequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatchBody(RequestBody):
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def check_patch(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        for field in type(self).model_fields:
            if field in self.model_fields_set and field not in self.nullable_fields and getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null")
        return self
