import os
from typing import List, Optional, Literal, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import (
    UserProfile,
    PantryItem,
    Meal,
    MealPlan,
    RestaurantQuery,
    Restaurant,
    CustomMealRequest,
    CustomMealResponse,
    ProductScanRequest,
    ProductScanResponse,
    PreferenceUpdate,
)

# Optional database helpers
try:
    from database import db, create_document, get_documents
except Exception:
    db = None
    def create_document(*args, **kwargs):
        return None
    def get_documents(*args, **kwargs):
        return []

app = FastAPI(title="Wellness & Food AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Wellness & Food AI Backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Not Initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------------- Section 1: Restaurant Finder ----------------------

@app.post("/api/restaurants/search", response_model=List[Restaurant])
def search_restaurants(query: RestaurantQuery):
    catalog = [
        {"name": "Green Garden", "cuisine": "Vegan", "rating": 4.6, "distance_km": 1.2, "price_range": "$$", "dietary_tags": ["vegan", "gluten-free"], "address": "12 Oak St"},
        {"name": "Pasta Palace", "cuisine": "Italian", "rating": 4.2, "distance_km": 2.5, "price_range": "$$", "dietary_tags": ["vegetarian"], "address": "77 Pine Ave"},
        {"name": "Sushi Sensei", "cuisine": "Japanese", "rating": 4.8, "distance_km": 0.8, "price_range": "$$$", "dietary_tags": ["pescatarian"], "address": "5 Market Rd"},
        {"name": "Budget Bites", "cuisine": "Mixed", "rating": 4.0, "distance_km": 1.0, "price_range": "$", "dietary_tags": ["vegan", "vegetarian"], "address": "3 King St"},
    ]
    budget_map = {"cheap": "$", "medium": "$$", "expensive": "$$$"}

    results = []
    for r in catalog:
        if query.cuisine_or_dish and query.cuisine_or_dish.lower() not in (r["cuisine"].lower() + " " + r["name"].lower()):
            continue
        if query.budget and r["price_range"] != budget_map.get(query.budget):
            continue
        results.append(r)
    return results

# ---------------- Section 2: Nutrition & Fitness Generator ----------------

class FitnessProgram(BaseModel):
    setting: Literal["home", "gym", "outdoor"]
    days: List[Dict[str, Any]]

class PlanResponse(BaseModel):
    daily_calorie_target: int
    meal_plan: MealPlan
    fitness_program: FitnessProgram


def calculate_calories(goal: str, weight_kg: Optional[float], height_cm: Optional[float], age: Optional[int], gender: Optional[str]):
    # Very rough BMR using Mifflin-St Jeor, defaults if missing
    w = weight_kg or 70
    h = height_cm or 170
    a = age or 30
    s = -161 if (gender or "female") == "female" else 5
    bmr = 10*w + 6.25*h - 5*a + s
    # activity factor moderate
    tdee = bmr * 1.45
    adj = {
        "lose": -400,
        "lean": -150,
        "build": 200,
        "bulk": 400,
        "maintain": 0,
    }.get(goal or "maintain", 0)
    return int(max(1200, tdee + adj))


def generate_meals(cal_target: int, diet_type: str, allergies: List[str], dislikes: List[str]) -> List[Meal]:
    base = [
        ("Oats with berries", ["oats", "almond milk", "berries", "chia"], 450, 18, 60, 12),
        ("Grilled chicken bowl", ["chicken", "quinoa", "broccoli", "olive oil"], 650, 45, 50, 20),
        ("Tofu stir-fry", ["tofu", "brown rice", "mixed veg", "soy sauce"], 600, 30, 70, 18),
        ("Salmon salad", ["salmon", "greens", "avocado", "vinaigrette"], 550, 35, 25, 28),
    ]
    meals: List[Meal] = []
    total = 0
    for title, ings, cals, p, c, f in base:
        if diet_type == "vegan" and ("chicken" in ings or "salmon" in ings):
            continue
        if diet_type == "vegetarian" and "chicken" in ings:
            continue
        if any(x.lower() in [i.lower() for i in ings] for x in allergies + dislikes):
            continue
        meals.append(Meal(title=title, ingredients=ings, calories=cals, protein_g=p, carbs_g=c, fats_g=f))
        total += cals
        if total >= cal_target:
            break
    if not meals:
        meals.append(Meal(title="Mixed veggie bowl", ingredients=["quinoa", "chickpeas", "veg"], calories=550, protein_g=22, carbs_g=70, fats_g=16))
    return meals


def build_groceries(meals: List[Meal]) -> List[str]:
    bag: Dict[str, int] = {}
    for m in meals:
        for ing in m.ingredients:
            bag[ing] = bag.get(ing, 0) + 1
    return [f"{k} x{v}" for k, v in bag.items()]


def gym_program(setting: str, goal: str) -> FitnessProgram:
    if setting == "home":
        days = [
            {"day": "Mon", "workout": ["Push-ups 4x12", "Squats 4x15", "Plank 3x60s"]},
            {"day": "Wed", "workout": ["Lunges 4x12", "Dips 4x10", "Crunches 3x20"]},
            {"day": "Fri", "workout": ["Burpees 4x10", "Glute bridge 4x15", "Side plank 3x45s"]},
        ]
    elif setting == "outdoor":
        days = [
            {"day": "Tue", "workout": ["Jog 30 min", "Hill sprints 8x20s", "Mobility 10 min"]},
            {"day": "Thu", "workout": ["Bike 40 min", "Push-ups 4x12", "Core 10 min"]},
            {"day": "Sat", "workout": ["Hike 60 min", "Stretch 15 min"]},
        ]
    else:
        days = [
            {"day": "Mon", "workout": ["Squat 5x5", "Bench 5x5", "Row 5x5"]},
            {"day": "Wed", "workout": ["Deadlift 3x5", "OHP 5x5", "Pull-ups 3xAMRAP"]},
            {"day": "Fri", "workout": ["Leg press 4x10", "Incline DB 4x10", "Lat pulldown 4x10"]},
        ]
    return FitnessProgram(setting=setting, days=days)


class GenerateRequest(BaseModel):
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[str] = None
    goal: Literal["lose weight", "get lean", "build muscle", "bulk", "maintain weight"]
    workout_preference: Literal["Home", "Gym", "Outdoor"]
    diet_type: Optional[Literal["omnivore", "vegan", "vegetarian", "gluten-free", "lactose-intolerant"]] = "omnivore"
    allergies: Optional[List[str]] = []
    dislikes: Optional[List[str]] = []

@app.post("/api/nutrition/generate", response_model=PlanResponse)
def generate_plan(req: GenerateRequest):
    goal_map = {
        "lose weight": "lose",
        "get lean": "lean",
        "build muscle": "build",
        "bulk": "bulk",
        "maintain weight": "maintain",
    }
    g = goal_map[req.goal]
    cal_target = calculate_calories(g, req.weight, req.height, req.age, req.gender)
    meals = generate_meals(cal_target, (req.diet_type or "omnivore"), req.allergies or [], req.dislikes or [])
    groceries = build_groceries(meals)

    plan = MealPlan(
        user_id=None,
        goal=g,
        diet_type=(req.diet_type or "omnivore"),
        daily_calorie_target=cal_target,
        meals=meals,
        groceries=groceries,
    )

    if db is not None:
        try:
            create_document("mealplan", plan)
        except Exception:
            pass

    program = gym_program(req.workout_preference.lower(), g)

    return PlanResponse(daily_calorie_target=cal_target, meal_plan=plan, fitness_program=program)

# View groceries quickly
@app.get("/api/nutrition/groceries", response_model=List[str])
def view_groceries():
    if db is None:
        raise HTTPException(status_code=404, detail="No stored plans yet")
    docs = get_documents("mealplan", limit=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No stored plans yet")
    return docs[-1].get("groceries", [])

# ---------------- Section 3: Custom Meal Builder ----------------

@app.post("/api/custom-meal", response_model=CustomMealResponse)
def custom_meal(req: CustomMealRequest):
    portions = max(1, req.portions)
    # Very naive mock nutrition, scale by portions
    base_nutrition = {
        "calories": 450,
        "protein_g": 25,
        "carbs_g": 60,
        "fats_g": 12,
    }
    nutrition = {k: float(v*portions) for k, v in base_nutrition.items()}
    # Ingredients mock
    ingredients = [f"{req.dish} ingredient {i+1}" for i in range(5)]
    return CustomMealResponse(ingredients=ingredients, nutrition=nutrition)

# ---------------- Section 4: Meal Plan Controls ----------------

@app.post("/api/meal-plan/regenerate", response_model=PlanResponse)
def regenerate_plan(req: GenerateRequest):
    return generate_plan(req)

@app.post("/api/preferences/update")
def update_preferences(pref: PreferenceUpdate):
    data = pref.model_dump()
    if db is not None:
        try:
            create_document("preferenceupdate", data)
        except Exception:
            pass
    return {"status": "ok", "saved": True}

# ---------------- Section 5: Smart Pantry ----------------

@app.post("/api/pantry/add")
def pantry_add(item: PantryItem):
    rid = None
    if db is not None:
        try:
            rid = create_document("pantryitem", item)
        except Exception:
            pass
    return {"status": "ok", "id": rid}

@app.get("/api/pantry/list", response_model=List[PantryItem])
def pantry_list():
    if db is None:
        return []
    docs = get_documents("pantryitem", {})
    out = []
    for d in docs:
        out.append(PantryItem(name=d.get("name", ""), quantity=d.get("quantity"), category=d.get("category")))
    return out

@app.get("/api/pantry/suggest", response_model=List[str])
def pantry_suggest():
    # Simple suggestion logic based on pantry items
    items = [p.name for p in pantry_list()] if db is not None else []
    if not items:
        return ["Veggie omelette", "Peanut butter toast", "Tomato pasta"]
    s = set([i.lower() for i in items])
    suggestions = []
    if {"pasta", "tomato"}.issubset(s):
        suggestions.append("Simple tomato pasta")
    if {"rice", "eggs"}.issubset(s):
        suggestions.append("Egg fried rice")
    if {"oats", "banana"}.issubset(s):
        suggestions.append("Banana oatmeal")
    return suggestions or ["Mixed grain bowl", "Stir-fry veggies"]

# Receipt OCR and Pantry Photo Upload (mocked)
class OCRRequest(BaseModel):
    image_base64: str

@app.post("/api/pantry/scan-receipt")
def scan_receipt(_: OCRRequest):
    # Mocked OCR extract
    items = ["milk", "eggs", "bread", "tomato", "pasta"]
    added = 0
    if db is not None:
        for it in items:
            try:
                create_document("pantryitem", PantryItem(name=it))
                added += 1
            except Exception:
                pass
    return {"status": "ok", "detected": items, "added": added}

@app.post("/api/pantry/photo")
def pantry_photo(_: OCRRequest):
    # Mocked vision detect
    detected = ["banana", "oats", "peanut butter"]
    added = 0
    if db is not None:
        for it in detected:
            try:
                create_document("pantryitem", PantryItem(name=it))
                added += 1
            except Exception:
                pass
    return {"status": "ok", "detected": detected, "added": added}

# ---------------- Section 6: Product Scanner ----------------

@app.post("/api/product/scan", response_model=ProductScanResponse)
def product_scan(req: ProductScanRequest):
    # Mock product heuristics from code
    code = req.code
    seed = sum([ord(c) for c in code])
    calories = 50 + (seed % 350)
    processed_percent = 10 + (seed % 80)
    rating = "Good" if processed_percent < 35 else ("Moderate" if processed_percent < 60 else "Avoid")
    return ProductScanResponse(calories=calories, processed_percent=processed_percent, health_rating=rating) 

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
