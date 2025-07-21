import os
import logging
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with A4F API
client = OpenAI(
    base_url="https://api.a4f.co/v1",
    api_key=os.getenv("A4F_API_KEY"),
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Hi! I\'m an AI image generation bot. Send me a text prompt and I\'ll create an image for you!\n\n'
        'Example: "a cat sitting on a rainbow"\n\n'
        'Use /help to see available commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *AI Image Generator Bot*

*Commands:*
/start - Start the bot
/help - Show this help message

*How to use:*
Simply send me any text description and I'll generate an image for you!

*Examples:*
• "a futuristic city at sunset"
• "a cute puppy playing in a garden"
• "abstract art with vibrant colors"
• "a mountain landscape with snow"

*Note:* Image generation may take 10-30 seconds.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate image from user prompt."""
    prompt = update.message.text.strip()
    
    if not prompt:
        await update.message.reply_text("Please provide a description for the image you want to generate.")
        return
    
    # Send "generating" message
    generating_msg = await update.message.reply_text("🎨 Generating your image... This may take a moment.")
    
    try:
        # Generate image using A4F API
        img_response = client.images.generate(
            model="provider-1/FLUX.1-kontext-pro",
            prompt=prompt,
            n=1,
            size="1024*1024"
        )
        
        image_url = img_response.data[0].url
        
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            # Send the image to user
            image_file = BytesIO(response.content)
            image_file.name = 'generated_image.png'
            
            await update.message.reply_photo(
                photo=image_file,
                caption=f"🎨 Generated image for: \"{prompt}\""
            )
            
            # Delete the "generating" message
            await generating_msg.delete()
            
        else:
            await generating_msg.edit_text("❌ Failed to download the generated image. Please try again.")
            
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        await generating_msg.edit_text(
            "❌ Sorry, there was an error generating your image. Please try again with a different prompt."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Get port from environment variable (required for Render)
    port = int(os.getenv("PORT", 8000))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://your-app-name.onrender.com/{bot_token}",
        url_path=bot_token
    )

if __name__ == '__main__':
    main()
