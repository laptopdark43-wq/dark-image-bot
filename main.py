import os
import logging
import requests
from io import BytesIO
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

# Initialize OpenAI client with A4F API
client = OpenAI(
    base_url="https://api.a4f.co/v1",
    api_key=os.getenv("A4F_API_KEY"),
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        '🤖 Hi! I\'m an AI image generation bot.\n\n'
        '🎨 **How to use:**\n'
        'Type `/imagine <your prompt>` to generate an image\n\n'
        '📝 **Example:**\n'
        '`/imagine a cat sitting on a rainbow`\n\n'
        '⚡ Use /help to see all available commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 **AI Image Generator Bot**

**Commands:**
• `/start` - Start the bot
• `/help` - Show this help message  
• `/imagine <prompt>` - Generate an image from your description

**How to use:**
Simply type `/imagine` followed by your description!

**Examples:**
• `/imagine a futuristic city at sunset`
• `/imagine a cute puppy playing in a garden`
• `/imagine abstract art with vibrant colors`
• `/imagine a mountain landscape with snow`

**Note:** Image generation may take 10-30 seconds.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def imagine_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate image from user prompt using /imagine command."""
    
    # Get the prompt from the command arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a description after the command!\n\n"
            "**Example:** `/imagine a beautiful sunset over mountains`",
            parse_mode='Markdown'
        )
        return
    
    # Join all arguments to form the complete prompt
    prompt = ' '.join(context.args).strip()
    
    if len(prompt) < 3:
        await update.message.reply_text("❌ Please provide a more detailed description.")
        return
    
    if len(prompt) > 1000:
        await update.message.reply_text("❌ Description too long. Please keep it under 1000 characters.")
        return
    
    # Send "generating" message
    generating_msg = await update.message.reply_text("🎨 Generating your image... This may take a moment.")
    
    try:
        # Generate image using A4F API
        logger.info(f"Generating image for prompt: {prompt}")
        img_response = client.images.generate(
            model="provider-1/FLUX.1-kontext-pro",
            prompt=prompt,
            n=1,
            size="1024*1024"
        )
        
        image_url = img_response.data[0].url
        logger.info(f"Generated image URL: {image_url}")
        
        # Try to send image by downloading first
        try:
            response = requests.get(image_url, timeout=30)
            logger.info(f"Download status: {response.status_code}")
            
            if response.status_code == 200 and len(response.content) > 0:
                # Successfully downloaded - send as file
                image_file = BytesIO(response.content)
                image_file.name = 'generated_image.png'
                
                await update.message.reply_photo(
                    photo=image_file,
                    caption=f"🎨 **Generated:** {prompt}"
                )
                await generating_msg.delete()
                logger.info("Image sent successfully via download method")
                
            else:
                # Download failed - fallback to URL
                raise Exception(f"Download failed: status {response.status_code}, size {len(response.content)}")
                
        except Exception as download_error:
            logger.warning(f"Download method failed: {download_error}")
            
            # Fallback: Send image URL directly
            try:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"🎨 **Generated:** {prompt}"
                )
                await generating_msg.delete()
                logger.info("Image sent successfully via URL method")
                
            except Exception as url_error:
                logger.error(f"URL method also failed: {url_error}")
                
                # Final fallback: Send URL as text
                await generating_msg.edit_text(
                    f"✅ **Image Generated Successfully!**\n\n"
                    f"**Prompt:** {prompt}\n\n"
                    f"**Image URL:** {image_url}\n\n"
                    f"🔗 Click the link above to view your generated image!"
                )
                logger.info("Sent image URL as text fallback")
            
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        await generating_msg.edit_text(
            "❌ Sorry, there was an error generating your image. Please try again with a different prompt."
        )

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages - remind users to use /imagine command."""
    await update.message.reply_text(
        "🎨 To generate an image, use the `/imagine` command!\n\n"
        "**Example:** `/imagine a beautiful landscape`\n\n"
        "Type /help for more information.",
        parse_mode='Markdown'
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
    
    if not os.getenv("A4F_API_KEY"):
        logger.error("A4F_API_KEY environment variable not set")
        return
    
    # Create the Application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("imagine", imagine_command))
    
    # Handle regular text messages (remind to use /imagine)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Get port from environment variable (required for Render)
    port = int(os.getenv("PORT", 8000))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
    webhook_url=f"https://your-actual-render-app-name.onrender.com/{bot_token}",
        url_path=bot_token
    )

if __name__ == '__main__':
    main()
