from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from config import OPENAI_API_KEY
from functions import get_joke, get_movie_info, convert_currency, get_sales_data
import json

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# Define available functions
AVAILABLE_FUNCTIONS = {
    "get_joke": get_joke,
    "get_movie_info": get_movie_info,
    "convert_currency": convert_currency,
    "get_sales_data": get_sales_data
}

# Function definitions for OpenAI
FUNCTION_DEFINITIONS = [
    {
        "name": "convert_currency",
        "description": "Convert an amount from one currency to another using current exchange rates",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The amount of money to convert"
                },
                "from_currency": {
                    "type": "string",
                    "description": "The currency code to convert from (e.g., USD, EUR, GBP)"
                },
                "to_currency": {
                    "type": "string",
                    "description": "The currency code to convert to (e.g., USD, EUR, GBP)"
                }
            },
            "required": ["amount", "from_currency", "to_currency"]
        }
    },
    {
        "name": "get_joke",
        "description": "Get a random joke",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_movie_info",
        "description": "Get information about a movie by its title",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the movie"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_sales_data",
        "description": "Get sales data from the store's database with optional date and product category filters",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (optional)"
                },
                "product_category": {
                    "type": "string",
                    "description": "Product category to filter by (optional)"
                }
            },
            "required": []
        }
    },
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('conversation_history', [])
    
    print("\n=== New Chat Request ===")
    print(f"User Message: {user_message}")
    print(f"Conversation History Length: {len(conversation_history)}")
    
    # Add user message to conversation
    conversation_history.append({"role": "user", "content": user_message})
    
    try:
        print("\n1. First OpenAI API Call (with function definitions):")
        print("Sending messages:", json.dumps(conversation_history, indent=2))
        
        # Get response from OpenAI using new syntax
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            functions=FUNCTION_DEFINITIONS,
            function_call="auto"
        )
        
        response_message = response.choices[0].message
        print("\nOpenAI Response:")
        print(json.dumps(response_message.model_dump(), indent=2))
        
        # Check if the model wants to call a function
        if response_message.function_call:
            function_name = response_message.function_call.name
            function_args = eval(response_message.function_call.arguments)
            
            print(f"\n2. Calling Function: {function_name}")
            print(f"Arguments: {function_args}")
            
            # Call the function
            function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
            print(f"Function Response: {function_response}")
            
            # Add function response to conversation
            conversation_history.append(response_message.model_dump())
            conversation_history.append({
                "role": "function",
                "name": function_name,
                "content": str(function_response)
            })
            
            print("\n3. Second OpenAI API Call (with function response):")
            print("Sending messages:", json.dumps(conversation_history, indent=2))
            
            # Get final response from OpenAI
            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_history
            )
            
            bot_response = second_response.choices[0].message.content
            print(f"\nFinal Bot Response: {bot_response}")
        else:
            print("\nNo function call needed")
            # No function call needed, just return the response
            bot_response = response_message.content
            print(f"Bot Response: {bot_response}")
        
        return jsonify({
            'response': bot_response,
            'conversation_history': conversation_history
        })
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 