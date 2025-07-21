import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with A4F API (same as your VS Code script)
client = OpenAI(
    base_url="https://api.a4f.co/v1",
    api_key=os.getenv("A4F_API_KEY"),
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        '🤖 **AI Image Generator Bot**\n\n'
        '🎨 **How to use:**\n'
        'Type `/imagine <your description>` to generate an image\n\n'
        '📝 **Example:**\n'
        '`/imagine a house in the mountain`\n\n'
        'The bot will return the image URL just like your VS Code script!',
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help information."""
    help_text = """
🤖 **AI Image Generator Bot**

**Commands:**
• `/start` - Start the bot
• `/help` - Show this help message  
• `/imagine <description>` - Generate an image

**Examples:**
• `/imagine a house in the mountain`
• `/imagine a cat sitting on a rainbow`
• `/imagine futuristic city at sunset`

**Note:** The bot returns image URLs in the same format as your VS Code script.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def imagine_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate image URL using A4F API (same as VS Code script)."""
    
    # Get the prompt from command arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a description!\n\n"
            "**Example:** `/imagine a house in the mountain`",
            parse_mode='Markdown'
        )
        return
    
    # Join arguments to form the prompt (same as prompt_1 in your script)
    prompt = ' '.join(context.args).strip()
    
    if len(prompt) < 3:
        await update.message.reply_text("❌ Please provide a more detailed description.")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🎨 Generating image URL...")
    
    try:
        # Exact same API call as your VS Code script
        img = client.images.generate(
            model="provider-1/FLUX.1-kontext-pro",
            prompt=prompt,
            n=1,
            size="1024*1024"
        )
        
        # Get the URL (same as your print statement)
        image_url = img.data[0].url
        
        # Log the URL (like your print statement)
        logger.info(f"Generated URL: {image_url}")
        
        # Send the URL to user
        await processing_msg.edit_text(
            f"✅ **Image Generated Successfully!**\n\n"
            f"**Prompt:** {prompt}\n\n"
            f"**Image URL:**\n`{image_url}`\n\n"
            f"🔗 Click the URL above to view your image!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        await processing_msg.edit_text(
            f"❌ **Error generating image:**\n`{str(e)}`\n\n"
            "Please try again with a different prompt.",
            parse_mode='Markdown'
        )

async def handle_regular_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    await update.message.reply_text(
        "🎨 To generate an image, use: `/imagine <description>`\n\n"
        "**Example:** `/imagine a house in the mountain`",
        parse_mode='Markdown'
    )

def main() -> None:
    """Start the bot."""
    # Get environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("A4F_API_KEY")
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
        
    if not api_key:
        logger.error("A4F_API_KEY not found in environment variables")
        return
    
    logger.info("Starting Telegram bot...")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("imagine", imagine_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_messages))
    
    # For Render deployment (webhook mode)
    port = int(os.getenv("PORT", 8000))
    app_name = os.getenv("RENDER_EXTERNAL_URL", "your-app-name.onrender.com")
    
    # Remove https:// if present
    if app_name.startswith("https://"):
        app_name = app_name[8:]
    if app_name.startswith("http://"):
        app_name = app_name[7:]
    
    webhook_url = f"https://{app_name}/{bot_token}"
    
    logger.info(f"Starting webhook on port {port}")
    logger.info(f"Webhook URL: {webhook_url}")
    
    # Run webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
        url_path=bot_token
    )

if __name__ == '__main__':
    main()
