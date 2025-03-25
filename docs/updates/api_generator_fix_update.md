# API Update: Async Generator and Constructor Parameter Fixes

This document details recent fixes made to the AI Hacker Discord bot codebase to resolve critical errors.

## Changes Overview

### 1. AIHandler.get_streaming_response Method

**Before:**
```python
async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                           user_id: Optional[int] = None, 
                           channel_id: Optional[int] = None,
                           guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
    # ... existing code ...
    
    # Clean the response for internal use
    cleaned_response = self._clean_response(response_buffer)
    return cleaned_response  # THIS WAS CAUSING THE ERROR
```

**After:**
```python
async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                           user_id: Optional[int] = None, 
                           channel_id: Optional[int] = None,
                           guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
    # ... existing code ...
    
    # Clean the response for internal use - but don't return it
    # Just store it if needed elsewhere
    self.last_cleaned_response = self._clean_response(response_buffer)
    # Instead of returning, we just end the generator
```

**Impact:**
- No change to existing functionality - all code that uses `get_streaming_response` with `async for` loops continues to work
- Added a new instance variable `last_cleaned_response` that can be accessed if needed after iterating through the generator

### 2. QuestionManager Constructor

**Before:**
```python
def __init__(self):
    # Ensure database directory exists
    os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
    self._ensure_db()
```

**After:**
```python
def __init__(self, bot=None):
    # Store bot instance
    self.bot = bot
    # Ensure database directory exists
    os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
    self._ensure_db()
```

**Impact:**
- The class now accepts a `bot` parameter that is stored for potential future use
- Existing initialization without parameters still works due to the default `None` value

### 3. NotionFAQ Constructor

**Before:**
```python
def __init__(self):
    self.client = Client(auth=NOTION_API_KEY)
    self.faq_page_id = NOTION_FAQ_PAGE_ID
    self._cache = None
    self._last_update = None
```

**After:**
```python
def __init__(self, api_key=None, page_id=None):
    self.client = Client(auth=api_key or NOTION_API_KEY)
    self.faq_page_id = page_id or NOTION_FAQ_PAGE_ID
    self._cache = None
    self._last_update = None
```

**Impact:**
- The class now accepts `api_key` and `page_id` parameters
- If not provided, it falls back to the global configuration values
- Allows for more flexible initialization with different credentials

### 4. Added Missing Moderation Queue Function

**Problem:**
The bot was trying to import a non-existent function:
```python
# In main.py
from app.services.moderation_queue import start_moderation_queue
await start_moderation_queue(bot)
```

**Solution:**
Added the missing function to the moderation_queue.py file:
```python
async def start_moderation_queue(bot=None):
    """
    Start the global moderation queue instance.
    
    Args:
        bot: Optional Discord bot instance
    """
    logger.info("Starting global moderation queue service")
    await moderation_queue.start()
    return moderation_queue
```

**Impact:**
- Fixed the ImportError that was preventing the bot from starting
- Added a utility function that properly starts the moderation queue service
- Returns the queue instance for potential use in other parts of the code

## Usage Examples

### Using the AIHandler.get_streaming_response

```python
async def handle_message(message_content):
    # Initialize the AI handler
    ai_handler = AIHandler()
    
    # Process the message and get chunks
    full_response = ""
    async for chunk in ai_handler.get_streaming_response(message_content):
        # Process each chunk as it arrives
        full_response += chunk
        # e.g., update UI with the chunk
        
    # If you need the cleaned response (without formatting instructions):
    # cleaned_response = ai_handler.last_cleaned_response
```

### Initializing QuestionManager

```python
# With a bot instance
question_manager = QuestionManager(bot)

# Without a bot instance (for testing/standalone usage)
question_manager = QuestionManager()
```

### Initializing NotionFAQ

```python
# With custom credentials
notion_faq = NotionFAQ(api_key="custom_api_key", page_id="custom_page_id")

# With default credentials from config
notion_faq = NotionFAQ()
```

### Using the Moderation Queue

```python
# In an async context (like on_ready event handler)
from app.services.moderation_queue import start_moderation_queue

# Start the queue service
queue = await start_moderation_queue(bot)

# Check queue status
status = queue.get_queue_status()
```

## Technical Notes

1. **Async Generators**:
   - In Python, async generator functions are identified by containing both `async def` and `yield`
   - They cannot use `return` with a value, only empty `return` statements to exit early

2. **Optional Parameters**:
   - All new parameters added to constructors are optional with default values
   - This ensures backward compatibility with existing code

3. **Module Exports**:
   - Always ensure that functions imported in one file are actually defined in the source module
   - When importing a function fails, check if it needs to be added to the source module

## Next Steps

No further action is required from frontend/client code. These changes are transparent and don't modify the public API interface.

If you have code that was previously expecting a return value from `get_streaming_response`, you'll need to update it to access `last_cleaned_response` after iterating through the async generator. 