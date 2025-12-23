from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra='forbid',
    )


class JobDescriptionConstants(CamelCaseModel):
    COMPANY_NAME_MIN_LENGTH: int
    COMPANY_NAME_MAX_LENGTH: int
    TITLE_MIN_LENGTH: int
    TITLE_MAX_LENGTH: int
    DESCRIPTION_TEXT_MIN_LENGTH: int
    DESCRIPTION_TEXT_MAX_LENGTH: int


class ResponseConstants(CamelCaseModel):
    AUDIO_MAX_SIZE_MEGABYTES: int
    AUDIO_MAX_DURATION_MINUTES: int


class Constants(CamelCaseModel):
    job_description_constants: JobDescriptionConstants
    response_constants: ResponseConstants
