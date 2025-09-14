from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
from ..models import Recipe, RecipeCreate, RecipeUpdate, RecipeIngredient, SupplyExpense
from ..models_sqlalchemy import Recipe as RecipeDB, SupplyExpense as SupplyExpenseDB
from ..database import get_db
from ..auth import get_current_admin

router = APIRouter(prefix="/recipes", tags=["recipes"])


# Helper function to calculate ingredient cost
def calculate_ingredient_cost(ingredient_id: str, quantity: float, unit: str, db: Session) -> float:
    """Calculate the cost of an ingredient based on supply expenses"""
    # Find the supply expense for this ingredient
    supply = db.query(SupplyExpenseDB).filter(
        SupplyExpenseDB.id == int(ingredient_id),
        SupplyExpenseDB.category == "Supply"
    ).first()
    
    if not supply:
        return 0.0

    # Find the most recent supply expense with the same item name and unit
    most_recent_supply = db.query(SupplyExpenseDB).filter(
        SupplyExpenseDB.category == "Supply",
        SupplyExpenseDB.items == supply.items,
        SupplyExpenseDB.purchaseUnit == supply.purchaseUnit,
        SupplyExpenseDB.pricePerUnit.isnot(None)
    ).order_by(SupplyExpenseDB.date.desc()).first()
    
    if not most_recent_supply or not most_recent_supply.pricePerUnit:
        return 0.0
    
    base_price_per_unit = most_recent_supply.pricePerUnit
    
    # Convert units if necessary
    if unit != most_recent_supply.purchaseUnit:
        purchase_unit = most_recent_supply.purchaseUnit
        if purchase_unit == 'kg' and unit == 'g':
            base_price_per_unit = base_price_per_unit / 1000
        elif purchase_unit == 'L' and unit == 'ml':
            base_price_per_unit = base_price_per_unit / 1000
        elif purchase_unit == 'g' and unit == 'kg':
            base_price_per_unit = base_price_per_unit * 1000
        elif purchase_unit == 'ml' and unit == 'L':
            base_price_per_unit = base_price_per_unit * 1000
    
    return quantity * base_price_per_unit

def calculate_recipe_costs(ingredients: List[RecipeIngredient], yield_quantity: float, db: Session):
    """Calculate total recipe costs"""
    ingredients_cost = sum(
        calculate_ingredient_cost(ingredient.ingredientId, ingredient.quantity, ingredient.unit, db)
        for ingredient in ingredients
    )
    
    total_cost = ingredients_cost
    cost_per_unit = total_cost / yield_quantity if yield_quantity > 0 else 0
    
    return {
        "ingredientsCost": ingredients_cost,
        "totalCost": total_cost,
        "costPerUnit": cost_per_unit
    }

@router.post("/", response_model=Recipe, summary="Create Recipe")
async def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new recipe"""
    # Calculate costs based on current ingredient prices
    costs = calculate_recipe_costs(
        recipe.ingredients, 
        recipe.yieldQuantity,
        db
    )
    
    db_recipe = RecipeDB(
        name=recipe.name,
        yieldQuantity=recipe.yieldQuantity,
        yieldUnitLabel=recipe.yieldUnitLabel,
        ingredients=json.dumps([ingredient.dict() for ingredient in recipe.ingredients]),
        totalCost=costs["totalCost"],
        costPerUnit=costs["costPerUnit"]
    )
    
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    return Recipe(
        id=str(db_recipe.id),
        name=db_recipe.name,
        yieldQuantity=db_recipe.yieldQuantity,
        yieldUnitLabel=db_recipe.yieldUnitLabel,
        ingredients=[RecipeIngredient(**ing) for ing in json.loads(db_recipe.ingredients)],
        totalCost=db_recipe.totalCost,
        costPerUnit=db_recipe.costPerUnit
    )

@router.get("/", response_model=List[Recipe], summary="Get All Recipes")
async def get_recipes(
    search: Optional[str] = Query(None, description="Search recipes by name"),
    db: Session = Depends(get_db)
):
    """Get all recipes with optional search"""
    query = db.query(RecipeDB)
    
    if search:
        query = query.filter(RecipeDB.name.ilike(f"%{search}%"))
    
    db_recipes = query.all()
    
    recipes = []
    for recipe in db_recipes:
        recipes.append(Recipe(
            id=str(recipe.id),
            name=recipe.name,
            yieldQuantity=recipe.yieldQuantity,
            yieldUnitLabel=recipe.yieldUnitLabel,
            ingredients=[RecipeIngredient(**ing) for ing in json.loads(recipe.ingredients)],
            totalCost=recipe.totalCost,
            costPerUnit=recipe.costPerUnit
        ))
    
    return recipes

@router.get("/{recipe_id}", response_model=Recipe, summary="Get Recipe by ID")
async def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get a specific recipe by ID"""
    db_recipe = db.query(RecipeDB).filter(RecipeDB.id == int(recipe_id)).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return Recipe(
        id=str(db_recipe.id),
        name=db_recipe.name,
        yieldQuantity=db_recipe.yieldQuantity,
        yieldUnitLabel=db_recipe.yieldUnitLabel,
        ingredients=[RecipeIngredient(**ing) for ing in json.loads(db_recipe.ingredients)],
        totalCost=db_recipe.totalCost,
        costPerUnit=db_recipe.costPerUnit
    )

@router.patch("/{recipe_id}", response_model=Recipe, summary="Update Recipe")
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a recipe"""
    db_recipe = db.query(RecipeDB).filter(RecipeDB.id == int(recipe_id)).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    update_data = recipe_update.dict(exclude_unset=True)
    
    # Handle ingredients update
    if "ingredients" in update_data:
        update_data["ingredients"] = json.dumps([ingredient.dict() if hasattr(ingredient, 'dict') else ingredient for ingredient in update_data["ingredients"]])
        
        # Recalculate costs if ingredients changed
        ingredients_list = [RecipeIngredient(**ing) for ing in json.loads(update_data["ingredients"])]
        costs = calculate_recipe_costs(
            ingredients_list,
            update_data.get("yieldQuantity", db_recipe.yieldQuantity),
            db
        )
        update_data["totalCost"] = costs["totalCost"]
        update_data["costPerUnit"] = costs["costPerUnit"]
    
    for field, value in update_data.items():
        setattr(db_recipe, field, value)
    
    db.commit()
    db.refresh(db_recipe)
    
    return Recipe(
        id=str(db_recipe.id),
        name=db_recipe.name,
        yieldQuantity=db_recipe.yieldQuantity,
        yieldUnitLabel=db_recipe.yieldUnitLabel,
        ingredients=[RecipeIngredient(**ing) for ing in json.loads(db_recipe.ingredients)],
        totalCost=db_recipe.totalCost,
        costPerUnit=db_recipe.costPerUnit
    )

@router.delete("/{recipe_id}", summary="Delete Recipe")
async def delete_recipe(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a recipe"""
    db_recipe = db.query(RecipeDB).filter(RecipeDB.id == int(recipe_id)).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    db.delete(db_recipe)
    db.commit()
    return {"message": "Recipe deleted successfully"}

@router.post("/{recipe_id}/calculate-costs", summary="Recalculate Recipe Costs")
async def recalculate_recipe_costs(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Recalculate recipe costs based on current ingredient prices"""
    db_recipe = db.query(RecipeDB).filter(RecipeDB.id == int(recipe_id)).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Get current ingredients and recalculate costs
    ingredients_list = [RecipeIngredient(**ing) for ing in json.loads(db_recipe.ingredients)]
    costs = calculate_recipe_costs(
        ingredients_list,
        db_recipe.yieldQuantity,
        db
    )
    
    # Update the recipe with new costs
    db_recipe.totalCost = costs["totalCost"]
    db_recipe.costPerUnit = costs["costPerUnit"]
    db.commit()
    db.refresh(db_recipe)
    
    return {
        "recipeId": recipe_id,
        "currentCosts": {
            "totalCost": costs["totalCost"],
            "costPerUnit": costs["costPerUnit"],
            "ingredientsCost": costs["ingredientsCost"]
        },
        "message": "Costs recalculated based on current supply prices"
    }

@router.get("/summary/costs", summary="Get Recipe Cost Summary")
async def get_recipe_cost_summary(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get summary of all recipe costs"""
    from sqlalchemy import func
    
    # Get aggregated data
    result = db.query(
        func.count(RecipeDB.id).label('total_recipes'),
        func.sum(RecipeDB.totalCost).label('total_recipe_value'),
        func.avg(RecipeDB.costPerUnit).label('avg_cost_per_unit')
    ).first()
    
    total_recipes = result.total_recipes or 0
    
    if total_recipes == 0:
        return {
            "totalRecipes": 0,
            "averageCostPerUnit": 0.0,
            "totalRecipeValue": 0.0,
            "mostExpensiveRecipe": None,
            "leastExpensiveRecipe": None
        }
    
    # Get most and least expensive recipes
    most_expensive = db.query(RecipeDB).order_by(RecipeDB.costPerUnit.desc()).first()
    least_expensive = db.query(RecipeDB).order_by(RecipeDB.costPerUnit.asc()).first()
    
    return {
        "totalRecipes": total_recipes,
        "averageCostPerUnit": round(result.avg_cost_per_unit or 0.0, 2),
        "totalRecipeValue": round(result.total_recipe_value or 0.0, 2),
        "mostExpensiveRecipe": {
            "name": most_expensive.name,
            "costPerUnit": most_expensive.costPerUnit
        } if most_expensive else None,
        "leastExpensiveRecipe": {
            "name": least_expensive.name,
            "costPerUnit": least_expensive.costPerUnit
        } if least_expensive else None
    }
