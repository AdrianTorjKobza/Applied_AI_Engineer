import os
import pandas as pd
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

# ==========================================
# 1. DEFINE THE DETERMINISTIC PYTHON TOOLS
# ==========================================

@tool
def calculate_subtotal(quantity: int, unit_price: float) -> float:
    """Calculates the subtotal by multiplying the quantity of items by their unit price."""
    return round(float(quantity) * float(unit_price), 2)

@tool
def apply_discount(subtotal: float, discount_percent: float) -> float:
    """Applies a percentage discount to the subtotal and returns the discounted amount.
    If discount_percent is 0, it returns the original subtotal."""
    if discount_percent == 0:
         return round(float(subtotal), 2)
    
    discount_amount = subtotal * (discount_percent / 100.0)

    return round(float(subtotal - discount_amount), 2)

@tool
def calculate_final_total(discounted_amount: float, shipping_fee: float) -> float:
    """Calculates the final total by adding the shipping fee to the discounted amount."""
    return round(float(discounted_amount) + float(shipping_fee), 2)

# Group the tools for the agent
tools = [calculate_subtotal, apply_discount, calculate_final_total]

# ==========================================
# 2. INITIALIZE LLM & AGENT
# ==========================================

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

system_prompt = """You are a precise accounting AI agent for a wholesale distributor. 
Your job is to read natural language emails from customers, extract numerical entities, and calculate the final invoice total.

Rules:
1. You MUST use the provided tools to calculate the subtotal, apply the discount, and add the shipping fee.
2. Do NOT do math in your head. Always rely on the tools.
3. If the email does NOT mention a discount percentage, assume the discount is 0%.
4. If the email does NOT mention a shipping or delivery fee, assume the fee is $0.
5. Execute the tools sequentially. Once you have the final calculated number from 'calculate_final_total', output ONLY that exact number as your final answer."""

agent_executor = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

# ==========================================
# 3. BATCH PROCESSING PIPELINE
# ==========================================

def process_emails(input_csv: str, output_csv: str):
    """Reads test data, executes the agent logic per row, and exports predictions."""
    print(f"Loading data from {input_csv}...")
    
    try:
        # Whether the file is comma-separated or tab-separated.
        df = pd.read_csv(input_csv, sep=None, engine='python') 
        
        # Strip any accidental whitespace from column names
        df.columns = df.columns.str.strip()
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_csv}. Please ensure the file exists.")
        return
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Double-check column names after parsing to give a clear warning if something is wrong
    if 'order_id' not in df.columns or 'email_text' not in df.columns:
        print(f"Error: Missing expected columns. Found columns: {list(df.columns)}")
        print("Please ensure your CSV file has headers named exactly 'order_id' and 'email_text'.")
        return

    predictions = []

    # Iterate through the DataFrame rows
    for index, row in df.iterrows():
        print(f"\n--- Processing Order ID: {row['order_id']} ---")
        email_text = row['email_text']
        
        try:
            response = agent_executor.invoke({"messages": [("user", email_text)]})
            final_answer = response["messages"][-1].content
            print(f"Agent Output: {final_answer}")
            
            predictions.append(final_answer)
            
        except Exception as e:
            print(f"Error processing Order ID {row['order_id']}: {e}")
            predictions.append("ERROR")

    # Append to DataFrame and export
    df['Total_Bill'] = predictions
    df.to_csv(output_csv, index=False)
    print(f"\n✅ Processing complete! Results successfully saved to {output_csv}.")

if __name__ == "__main__":
    # Ensure paths align with your data directory directory layout
    process_emails("data/test.csv", "data/predictions.csv")