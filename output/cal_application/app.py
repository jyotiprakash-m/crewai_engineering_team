import gradio as gr
from Calculator import Calculator

calculator = Calculator()

def perform_calculation(num1, num2, operation):
    try:
        num1 = float(num1)
        num2 = float(num2)
        
        if operation == "Addition":
            result = calculator.add(num1, num2)
        elif operation == "Subtraction":
            result = calculator.subtract(num1, num2)
        elif operation == "Multiplication":
            result = calculator.multiply(num1, num2)
        elif operation == "Division":
            try:
                result = calculator.divide(num1, num2)
            except ValueError as e:
                return str(e)
        
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks(title="Simple Calculator") as demo:
    gr.Markdown("# Simple Calculator")
    gr.Markdown("Enter two numbers and select an operation")
    
    with gr.Row():
        num1 = gr.Number(label="First Number")
        num2 = gr.Number(label="Second Number")
    
    operation = gr.Dropdown(
        choices=["Addition", "Subtraction", "Multiplication", "Division"],
        label="Operation",
        value="Addition"
    )
    
    calculate_btn = gr.Button("Calculate")
    result = gr.Textbox(label="Result")
    
    calculate_btn.click(
        fn=perform_calculation,
        inputs=[num1, num2, operation],
        outputs=result
    )

if __name__ == "__main__":
    demo.launch()