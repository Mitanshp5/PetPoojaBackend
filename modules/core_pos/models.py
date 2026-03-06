from typing import Optional, List, Annotated, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import core_schema
from bson import ObjectId

class _ObjectIdPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str | ObjectId) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError("Invalid ObjectId")

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

PyObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class MenuItemModel(MongoBaseModel):
    name: str
    description: Optional[str] = ""
    selling_price: float
    food_cost: float
    is_active: bool = True
    category: str
    veg: bool = True


class OrderItemModel(BaseModel):
    menu_item_id: str
    name: str
    qty: int = 1
    modifiers: Optional[List[str]] = []
    notes: Optional[str] = None

class OrderModel(MongoBaseModel):
    orderNumber: str
    items: List[OrderItemModel] = []
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    status: str = "new"  # new, preparing, ready, served
    type: str = "dine-in" # dine-in, takeaway, delivery
    table: Optional[str] = None
    time: str
    elapsed: int = 0
