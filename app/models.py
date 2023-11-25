from typing import Optional
from pydantic import ConfigDict, BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated
from bson import ObjectId

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class ShareholderModel(BaseModel):
    """
    A shareholder document in the database.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    shares: int = Field(...)
    transactions: list[int] = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class UpdateShareholderModel(BaseModel):
    """
    A set of optional updates to be made to a shareholder document in the database.
    """
    name: Optional[str] = None
    shares: Optional[int] = None
    transactions: Optional[list[int]] = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )