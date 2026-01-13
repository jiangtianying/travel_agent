import gradio as gr
from backend import chat, reset_chat, change_model
from model_provider import get_available_models, get_current_model, AVAILABLE_MODELS


def create_app():
    """Create the Gradio application."""
    with gr.Blocks(title="Travel Agent AI") as app:
        gr.Markdown(
            """
            # Travel Agent AI

            Welcome! I'm your personal travel planning assistant. I can help you:
            - Search for flights and hotels
            - Find attractions and restaurants
            - Create detailed travel itineraries
            - Optimize your travel plans based on your feedback

            **Just tell me where you want to go and when!**

            *Traces are sent to [OpenAI Traces Dashboard](https://platform.openai.com/traces) under workflow "travel_agent"*
            """
        )

        with gr.Row():
            model_dropdown = gr.Dropdown(
                choices=get_available_models(),
                value=AVAILABLE_MODELS[get_current_model()]["display_name"],
                label="Select Model",
                scale=2,
            )
            model_status = gr.Textbox(
                value="",
                label="Status",
                interactive=False,
                scale=1,
            )

        chatbot = gr.Chatbot(
            label="Travel Assistant",
            height=500,
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your message",
                placeholder="E.g., 'I want to plan a 5-day trip to Tokyo in March'",
                lines=2,
                scale=4,
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("Clear Chat", variant="secondary")

        with gr.Accordion("Example Prompts", open=False):
            gr.Examples(
                examples=[
                    ["I want to plan a 7-day trip to Paris in April with a budget of $2000"],
                    ["Help me find the cheapest flights from New York to London for next month"],
                    ["I'm looking for a romantic getaway in Italy for 5 days"],
                    ["Plan a family vacation to Orlando, Florida with kids-friendly activities"],
                    ["I need a business trip itinerary for 3 days in Singapore"],
                ],
                inputs=msg,
                label="Click on an example to try it",
            )

        def respond(message, history):
            if not message.strip():
                return history, ""
            response = chat(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return history, ""

        def clear():
            reset_chat()
            return []

        def on_model_change(model_name):
            result = change_model(model_name)
            return result

        model_dropdown.change(on_model_change, [model_dropdown], [model_status])
        msg.submit(respond, [msg, chatbot], [chatbot, msg])
        submit_btn.click(respond, [msg, chatbot], [chatbot, msg])
        clear_btn.click(clear, outputs=[chatbot])

    return app


def main():
    """Main entry point."""
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
    )


if __name__ == "__main__":
    main()
