"""
Utilities for ingredient processing, quantity parsing, and categorization.
"""
import re
from typing import Dict, List, Optional, Tuple
from fractions import Fraction


# Ingredient categorization mapping
INGREDIENT_CATEGORIES = {
    'produce': [
        'apple', 'banana', 'orange', 'lemon', 'lime', 'tomato', 'onion', 'garlic',
        'carrot', 'celery', 'potato', 'lettuce', 'spinach', 'broccoli', 'bell pepper',
        'mushroom', 'avocado', 'cucumber', 'zucchini', 'eggplant', 'corn', 'peas',
        'green beans', 'asparagus', 'cabbage', 'cauliflower', 'kale', 'arugula',
        'basil', 'parsley', 'cilantro', 'mint', 'rosemary', 'thyme', 'oregano',
        'dill', 'sage', 'chives', 'scallion', 'leek', 'shallot', 'ginger', 'jalapeno'
    ],
    'meat': [
        'chicken', 'beef', 'pork', 'turkey', 'lamb', 'fish', 'salmon', 'tuna',
        'shrimp', 'crab', 'lobster', 'bacon', 'sausage', 'ham', 'ground beef',
        'ground turkey', 'ground pork', 'steak', 'roast', 'wings', 'thighs'
    ],
    'dairy': [
        'milk', 'butter', 'cheese', 'cream', 'yogurt', 'sour cream', 'heavy cream',
        'cream cheese', 'cottage cheese', 'ricotta', 'mozzarella', 'cheddar',
        'parmesan', 'swiss', 'feta', 'goat cheese', 'blue cheese', 'eggs'
    ],
    'pantry': [
        'flour', 'sugar', 'salt', 'pepper', 'oil', 'vinegar', 'baking powder',
        'baking soda', 'vanilla', 'honey', 'maple syrup', 'soy sauce', 'hot sauce',
        'worcestershire', 'mustard', 'ketchup', 'mayonnaise', 'pasta', 'rice',
        'quinoa', 'oats', 'bread', 'crackers', 'nuts', 'almonds', 'walnuts',
        'pecans', 'cashews', 'peanuts', 'coconut', 'chocolate', 'cocoa powder'
    ],
    'canned_goods': [
        'beans', 'chickpeas', 'lentils', 'tomato sauce', 'tomato paste', 'diced tomatoes',
        'coconut milk', 'chicken broth', 'beef broth', 'vegetable broth', 'stock',
        'corn', 'green beans', 'peas', 'artichokes', 'olives', 'tuna', 'salmon'
    ],
    'frozen': [
        'frozen vegetables', 'frozen fruit', 'frozen berries', 'ice cream',
        'frozen pizza', 'frozen chicken', 'frozen fish', 'frozen shrimp'
    ],
    'beverages': [
        'water', 'juice', 'soda', 'coffee', 'tea', 'wine', 'beer', 'liquor',
        'coconut water', 'almond milk', 'soy milk', 'oat milk'
    ],
    'spices': [
        'cinnamon', 'paprika', 'cumin', 'chili powder', 'garlic powder',
        'onion powder', 'red pepper flakes', 'black pepper', 'white pepper',
        'cayenne', 'turmeric', 'garam masala', 'curry powder', 'bay leaves',
        'nutmeg', 'cardamom', 'cloves', 'allspice', 'fennel', 'coriander'
    ],
    'condiments': [
        'mustard', 'ketchup', 'mayonnaise', 'ranch', 'bbq sauce', 'teriyaki',
        'salsa', 'hot sauce', 'sriracha', 'pesto', 'tahini', 'hummus'
    ]
}

# Unit conversion factors (all to base units)
UNIT_CONVERSIONS = {
    # Volume conversions (to milliliters)
    'volume': {
        'tsp': 4.92892, 'teaspoon': 4.92892, 'teaspoons': 4.92892,
        'tbsp': 14.7868, 'tablespoon': 14.7868, 'tablespoons': 14.7868,
        'fl oz': 29.5735, 'fluid ounce': 29.5735, 'fluid ounces': 29.5735,
        'cup': 236.588, 'cups': 236.588,
        'pt': 473.176, 'pint': 473.176, 'pints': 473.176,
        'qt': 946.353, 'quart': 946.353, 'quarts': 946.353,
        'gal': 3785.41, 'gallon': 3785.41, 'gallons': 3785.41,
        'ml': 1, 'milliliter': 1, 'milliliters': 1,
        'l': 1000, 'liter': 1000, 'liters': 1000,
        'dl': 100, 'deciliter': 100, 'deciliters': 100
    },
    # Weight conversions (to grams)
    'weight': {
        'oz': 28.3495, 'ounce': 28.3495, 'ounces': 28.3495,
        'lb': 453.592, 'pound': 453.592, 'pounds': 453.592,
        'g': 1, 'gram': 1, 'grams': 1,
        'kg': 1000, 'kilogram': 1000, 'kilograms': 1000,
        'mg': 0.001, 'milligram': 0.001, 'milligrams': 0.001
    },
    # Count units (no conversion)
    'count': {
        'piece': 1, 'pieces': 1, 'item': 1, 'items': 1,
        'clove': 1, 'cloves': 1, 'head': 1, 'heads': 1,
        'bunch': 1, 'bunches': 1, 'stalk': 1, 'stalks': 1,
        'slice': 1, 'slices': 1, 'leaf': 1, 'leaves': 1
    }
}

# Common ingredient synonyms for merging
INGREDIENT_SYNONYMS = {
    'green onion': ['scallion', 'spring onion', 'green onions', 'scallions'],
    'bell pepper': ['sweet pepper', 'capsicum', 'bell peppers', 'sweet peppers'],
    'cilantro': ['coriander leaves', 'fresh coriander', 'chinese parsley'],
    'heavy cream': ['heavy whipping cream', 'double cream', 'thick cream'],
    'ground beef': ['minced beef', 'beef mince', 'hamburger meat'],
    'soy sauce': ['shoyu', 'light soy sauce', 'dark soy sauce'],
    'tomato paste': ['tomato puree', 'concentrated tomato'],
    'chicken broth': ['chicken stock', 'chicken bouillon'],
    'vegetable broth': ['vegetable stock', 'veggie broth']
}


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient name for consistent matching.
    
    Args:
        name: Raw ingredient name.
        
    Returns:
        Normalized ingredient name.
    """
    name = name.lower().strip()
    
    # Check synonyms and use canonical form
    for canonical, synonyms in INGREDIENT_SYNONYMS.items():
        if name in synonyms or name == canonical:
            return canonical
    
    # Remove common descriptors that don't affect shopping
    descriptors_to_remove = [
        'fresh', 'dried', 'frozen', 'canned', 'organic', 'raw',
        'cooked', 'chopped', 'diced', 'sliced', 'minced', 'grated',
        'ground', 'whole', 'extra', 'large', 'small', 'medium'
    ]
    
    words = name.split()
    filtered_words = [w for w in words if w not in descriptors_to_remove]
    
    return ' '.join(filtered_words) if filtered_words else name


def parse_quantity(quantity_str: str) -> Tuple[float, Optional[str]]:
    """
    Parse quantity string to extract amount and unit.
    
    Args:
        quantity_str: Quantity string like "2 cups", "1/2 tsp", "3 large eggs".
        
    Returns:
        Tuple of (amount, unit) where unit can be None.
    """
    if not quantity_str or not quantity_str.strip():
        return 1.0, None
    
    quantity_str = quantity_str.lower().strip()
    
    # Pattern to match fractions, decimals, and mixed numbers
    # Examples: "2", "1/2", "2.5", "1 1/2", "2-3", "2 to 3"
    fraction_pattern = r'(\d+(?:\s+\d+/\d+|\.\d+|/\d+)?)'
    unit_pattern = r'([a-zA-Z]+\.?)'
    
    # Try to match quantity and unit
    match = re.match(
        fr'^\s*{fraction_pattern}\s*{unit_pattern}?\s*',
        quantity_str
    )
    
    if not match:
        # If no match, assume quantity is 1
        return 1.0, None
    
    amount_str = match.group(1).strip()
    unit = match.group(2).strip() if match.group(2) else None
    
    # Parse the amount (handle fractions and mixed numbers)
    try:
        amount = float(Fraction(amount_str.replace(' ', '+')))
    except (ValueError, ZeroDivisionError):
        amount = 1.0
    
    # Clean up unit
    if unit:
        unit = unit.rstrip('.,').lower()
        # Handle plural forms
        if unit.endswith('s') and unit not in ['cups', 'tablespoons', 'teaspoons']:
            singular = unit[:-1]
            if any(singular in units for units in UNIT_CONVERSIONS.values()):
                unit = singular
    
    return amount, unit


def get_unit_type(unit: Optional[str]) -> str:
    """
    Determine if a unit is volume, weight, or count.
    
    Args:
        unit: Unit string.
        
    Returns:
        Unit type: 'volume', 'weight', or 'count'.
    """
    if not unit:
        return 'count'
    
    unit = unit.lower()
    
    for unit_type, units in UNIT_CONVERSIONS.items():
        if unit in units:
            return unit_type
    
    return 'count'


def convert_to_base_unit(amount: float, unit: Optional[str]) -> Tuple[float, str]:
    """
    Convert amount and unit to base unit for the unit type.
    
    Args:
        amount: Quantity amount.
        unit: Unit string.
        
    Returns:
        Tuple of (converted_amount, base_unit).
    """
    if not unit:
        return amount, 'pieces'
    
    unit = unit.lower()
    unit_type = get_unit_type(unit)
    
    if unit_type == 'count':
        return amount, 'pieces'
    
    conversions = UNIT_CONVERSIONS[unit_type]
    
    if unit in conversions:
        converted_amount = amount * conversions[unit]
        base_unit = 'ml' if unit_type == 'volume' else 'g'
        return converted_amount, base_unit
    
    # If unit not found, return as is
    return amount, unit


def can_merge_ingredients(ingredient1: dict, ingredient2: dict) -> bool:
    """
    Check if two ingredients can be merged based on name similarity and unit compatibility.
    
    Args:
        ingredient1: First ingredient dict with 'name', 'amount', 'unit'.
        ingredient2: Second ingredient dict with 'name', 'amount', 'unit'.
        
    Returns:
        True if ingredients can be merged.
    """
    name1 = normalize_ingredient_name(ingredient1.get('name', ''))
    name2 = normalize_ingredient_name(ingredient2.get('name', ''))
    
    if name1 != name2:
        return False
    
    unit1 = ingredient1.get('unit')
    unit2 = ingredient2.get('unit')
    
    # Same unit type (volume, weight, count)
    return get_unit_type(unit1) == get_unit_type(unit2)


def merge_ingredients(ingredients: List[dict]) -> dict:
    """
    Merge a list of similar ingredients into one aggregated ingredient.
    
    Args:
        ingredients: List of ingredient dicts to merge.
        
    Returns:
        Merged ingredient dict.
    """
    if not ingredients:
        raise ValueError("Cannot merge empty ingredient list")
    
    if len(ingredients) == 1:
        return ingredients[0].copy()
    
    # Use the first ingredient as base
    base = ingredients[0].copy()
    base_name = normalize_ingredient_name(base.get('name', ''))
    base_amount = base.get('amount', 1.0)
    base_unit = base.get('unit')
    
    # Convert base to common unit
    total_base_amount, common_unit = convert_to_base_unit(base_amount, base_unit)
    
    recipe_names = [base.get('recipe_name', 'Unknown')]
    notes = []
    
    if base.get('notes'):
        notes.append(base['notes'])
    
    # Merge additional ingredients
    for ingredient in ingredients[1:]:
        amount = ingredient.get('amount', 1.0)
        unit = ingredient.get('unit')
        
        # Convert to same unit system
        converted_amount, converted_unit = convert_to_base_unit(amount, unit)
        
        if get_unit_type(converted_unit) == get_unit_type(common_unit):
            total_base_amount += converted_amount
        else:
            # Can't convert units, add as note
            notes.append(f"Additional: {amount} {unit or ''}")
        
        if ingredient.get('recipe_name'):
            recipe_names.append(ingredient['recipe_name'])
        
        if ingredient.get('notes'):
            notes.append(ingredient['notes'])
    
    # Format the final amount nicely
    if common_unit in ['ml', 'g']:
        # Convert back to more readable units
        if common_unit == 'ml':
            if total_base_amount >= 1000:
                final_amount = total_base_amount / 1000
                final_unit = 'l'
            elif total_base_amount >= 236.588:  # About 1 cup
                final_amount = total_base_amount / 236.588
                final_unit = 'cups'
            else:
                final_amount = total_base_amount
                final_unit = 'ml'
        else:  # grams
            if total_base_amount >= 1000:
                final_amount = total_base_amount / 1000
                final_unit = 'kg'
            elif total_base_amount >= 453.592:  # About 1 pound
                final_amount = total_base_amount / 453.592
                final_unit = 'lb'
            else:
                final_amount = total_base_amount
                final_unit = 'g'
        
        # Round to reasonable precision
        if final_amount >= 10:
            amount_str = f"{final_amount:.0f}"
        elif final_amount >= 1:
            amount_str = f"{final_amount:.1f}"
        else:
            amount_str = f"{final_amount:.2f}"
    else:
        final_amount = total_base_amount
        final_unit = common_unit
        if final_amount == int(final_amount):
            amount_str = str(int(final_amount))
        else:
            amount_str = f"{final_amount:.1f}"
    
    return {
        'name': base_name,
        'total_amount': amount_str,
        'unit': final_unit,
        'notes': list(set(notes)),  # Remove duplicates
        'recipe_names': list(set(recipe_names))  # Remove duplicates
    }


def categorize_ingredient(ingredient_name: str) -> str:
    """
    Categorize an ingredient based on its name.
    
    Args:
        ingredient_name: Name of the ingredient.
        
    Returns:
        Category name (produce, meat, dairy, etc.).
    """
    name_lower = normalize_ingredient_name(ingredient_name)
    
    for category, items in INGREDIENT_CATEGORIES.items():
        for item in items:
            if item in name_lower or name_lower in item:
                return category
    
    # Default category for unknown ingredients
    return 'other'


def aggregate_recipe_ingredients(recipes: List[dict]) -> List[dict]:
    """
    Aggregate ingredients from multiple recipes, merging similar ingredients.
    
    Args:
        recipes: List of recipe dicts with 'name' and 'ingredients' fields.
        
    Returns:
        List of aggregated ingredient dicts.
    """
    all_ingredients = []
    
    # Extract all ingredients from all recipes
    for recipe in recipes:
        recipe_name = recipe.get('title', recipe.get('name', 'Unknown Recipe'))
        ingredients = recipe.get('ingredients', [])
        
        for ingredient in ingredients:
            # Parse ingredient if it's a string
            if isinstance(ingredient, str):
                # Try to parse "amount unit name" format
                parts = ingredient.split(' ', 2)
                if len(parts) >= 2:
                    amount_str = parts[0]
                    unit = parts[1] if len(parts) > 2 else None
                    name = ' '.join(parts[2:]) if len(parts) > 2 else parts[1]
                    
                    amount, parsed_unit = parse_quantity(f"{amount_str} {unit}" if unit else amount_str)
                    
                    ingredient_dict = {
                        'name': name,
                        'amount': amount,
                        'unit': parsed_unit or unit,
                        'recipe_name': recipe_name,
                        'notes': ingredient  # Keep original for reference
                    }
                else:
                    ingredient_dict = {
                        'name': ingredient,
                        'amount': 1.0,
                        'unit': None,
                        'recipe_name': recipe_name,
                        'notes': ingredient
                    }
            elif isinstance(ingredient, dict):
                # Already structured ingredient
                amount, unit = parse_quantity(ingredient.get('amount', '1'))
                ingredient_dict = {
                    'name': ingredient.get('name', ingredient.get('ingredient', 'Unknown')),
                    'amount': amount,
                    'unit': unit,
                    'recipe_name': recipe_name,
                    'notes': ingredient.get('notes', '')
                }
            else:
                continue
            
            all_ingredients.append(ingredient_dict)
    
    # Group similar ingredients
    ingredient_groups = []
    used_indices = set()
    
    for i, ingredient in enumerate(all_ingredients):
        if i in used_indices:
            continue
        
        # Find all similar ingredients
        similar_ingredients = [ingredient]
        used_indices.add(i)
        
        for j, other_ingredient in enumerate(all_ingredients[i + 1:], start=i + 1):
            if j in used_indices:
                continue
            
            if can_merge_ingredients(ingredient, other_ingredient):
                similar_ingredients.append(other_ingredient)
                used_indices.add(j)
        
        # Merge the similar ingredients
        if len(similar_ingredients) > 1:
            merged = merge_ingredients(similar_ingredients)
        else:
            # Single ingredient, format consistently
            ing = similar_ingredients[0]
            merged = {
                'name': normalize_ingredient_name(ing['name']),
                'total_amount': str(ing['amount']),
                'unit': ing['unit'],
                'notes': [ing['notes']] if ing['notes'] else [],
                'recipe_names': [ing['recipe_name']]
            }
        
        ingredient_groups.append(merged)
    
    return ingredient_groups


def group_ingredients_by_category(ingredients: List[dict]) -> Dict[str, List[dict]]:
    """
    Group aggregated ingredients by shopping category.
    
    Args:
        ingredients: List of aggregated ingredient dicts.
        
    Returns:
        Dict mapping category names to ingredient lists.
    """
    categorized = {}
    
    for ingredient in ingredients:
        category = categorize_ingredient(ingredient['name'])
        
        if category not in categorized:
            categorized[category] = []
        
        categorized[category].append(ingredient)
    
    # Sort categories by common shopping order
    category_order = [
        'produce', 'meat', 'dairy', 'frozen', 'canned_goods',
        'pantry', 'spices', 'condiments', 'beverages', 'other'
    ]
    
    ordered_groups = {}
    for category in category_order:
        if category in categorized:
            ordered_groups[category] = sorted(
                categorized[category],
                key=lambda x: x['name']
            )
    
    # Add any remaining categories not in the standard order
    for category, ingredients in categorized.items():
        if category not in ordered_groups:
            ordered_groups[category] = sorted(ingredients, key=lambda x: x['name'])
    
    return ordered_groups