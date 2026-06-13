from __future__ import annotations

from fastapi import HTTPException

from app.data import CAFETERIA_TIMINGS, MENU


class CafeteriaServer:
    source = "campus_cafeteria"

    def get_menu(self, meal: str = "lunch") -> dict:
        meal_key = meal.lower()
        if meal_key not in MENU:
            raise HTTPException(status_code=404, detail=f"No menu found for meal '{meal}'.")
        return {"meal": meal_key, "items": MENU[meal_key], "timing": CAFETERIA_TIMINGS[meal_key]}

    def all_menus(self) -> dict:
        return {
            meal: {"items": items, "timing": CAFETERIA_TIMINGS[meal]}
            for meal, items in MENU.items()
        }


cafeteria_server = CafeteriaServer()
