import requests
import json
from datetime import datetime
from config import OMDB_API_KEY
import pandas as pd
from typing import Optional

def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Convert currency using public exchange rate API"""
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        rate = data["rates"][to_currency]
        converted_amount = amount * rate
        
        return {
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": round(converted_amount, 2),
            "to_currency": to_currency,
            "rate": rate
        }
    except Exception as e:
        return {"error": str(e)}

def get_joke(category: str = None):
    """Get a random joke from JokeAPI"""
    base_url = "https://v2.jokeapi.dev/joke/"
    
    # Available categories: Programming, Misc, Pun, Spooky, Christmas
    category = category if category else "Programming"
    
    try:
        response = requests.get(f"{base_url}{category}?safe-mode")
        response.raise_for_status()
        data = response.json()
        
        if data["type"] == "single":
            return {
                "joke": data["joke"],
                "category": data["category"]
            }
        else:
            return {
                "setup": data["setup"],
                "delivery": data["delivery"],
                "category": data["category"]
            }
    except Exception as e:
        return {"error": str(e)}

def get_movie_info(title: str, year: str = None):
    """Get movie information from OMDB API"""
    base_url = "http://www.omdbapi.com/"
    
    params = {
        "apikey": OMDB_API_KEY,
        "t": title,
        "y": year if year else None
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Response") == "True":
            return {
                "title": data["Title"],
                "year": data["Year"],
                "rating": data["imdbRating"],
                "plot": data["Plot"],
                "director": data["Director"],
                "actors": data["Actors"]
            }
        else:
            return {"error": "Movie not found"}
    except Exception as e:
        return {"error": str(e)}

def get_sales_data(date: Optional[str] = None, product_category: Optional[str] = None):
    """Get sales data from store's CSV database"""
    try:
        # Read the CSV file
        df = pd.read_csv('data/sales_data.csv')
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date if provided
        if date:
            query_date = pd.to_datetime(date)
            df = df[df['date'].dt.date == query_date.date()]
            
        # Filter by product category if provided
        if product_category:
            df = df[df['category'].str.lower() == product_category.lower()]
        
        # Calculate summary statistics
        summary = {
            "total_sales": float(df['amount'].sum()),
            "total_orders": len(df),
            "average_order_value": float(df['amount'].mean()),
            "products_sold": int(df['quantity'].sum())
        }
        
        if df.empty:
            return {"error": "No data found for the specified criteria"}
            
        return summary
        
    except FileNotFoundError:
        return {"error": "Sales data file not found"}
    except Exception as e:
        return {"error": str(e)}