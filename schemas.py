"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict

# User profile and preferences
class UserProfile(BaseModel):
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    age: Optional[int] = Field(None, ge=0, le=120)
    weight_kg: Optional[float] = Field(None, ge=0)
    height_cm: Optional[float] = Field(None, ge=0)
    gender: Optional[Literal["male", "female", "other"]] = None
    goal: Optional[Literal["lose", "lean", "build", "bulk", "maintain"]] = None
    workout_preference: Optional[Literal["home", "gym", "outdoor"]] = None
    diet_type: Optional[Literal["omnivore", "vegan", "vegetarian", "gluten-free", "lactose-intolerant"]] = Field("omnivore")
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)

# Pantry inventory
class PantryItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    category: Optional[str] = None

# Meal plan structures
class Meal(BaseModel):
    title: str
    ingredients: List[str]
    calories: int
    protein_g: int
    carbs_g: int
    fats_g: int

class MealPlan(BaseModel):
    user_id: Optional[str] = None
    goal: Literal["lose", "lean", "build", "bulk", "maintain"]
    diet_type: Literal["omnivore", "vegan", "vegetarian", "gluten-free", "lactose-intolerant"]
    daily_calorie_target: int
    meals: List[Meal]
    groceries: List[str]

# Restaurant search
class RestaurantQuery(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cuisine_or_dish: Optional[str] = None
    budget: Optional[Literal["cheap", "medium", "expensive"]] = None

class Restaurant(BaseModel):
    name: str
    cuisine: str
    rating: float
    distance_km: float
    price_range: str
    dietary_tags: List[str]
    address: Optional[str] = None

# Custom meal builder
class CustomMealRequest(BaseModel):
    dish: str
    portions: int
    diet_type: Optional[Literal["omnivore", "vegan", "vegetarian", "gluten-free", "lactose-intolerant"]] = "omnivore"

class CustomMealResponse(BaseModel):
    ingredients: List[str]
    nutrition: Dict[str, float]

# Product scan
class ProductScanRequest(BaseModel):
    code: str

class ProductScanResponse(BaseModel):
    calories: int
    processed_percent: int
    health_rating: Literal["Good", "Moderate", "Avoid"]

# Preferences update
class PreferenceUpdate(BaseModel):
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    diet_type: Optional[Literal["omnivore", "vegan", "vegetarian", "gluten-free", "lactose-intolerant"]] = None

# Example schemas retained for reference (not used by app directly)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
