# Violation Category Mapping Update

## Overview
This update enhances the Discord bot's content moderation system by adding support for OpenAI API's underscore-based violation category keys in addition to the original slash-based keys. This ensures that all violation categories returned by the OpenAI Moderation API are properly translated to Chinese in notifications.

## Changes

### 1. Community Guidelines
Updated `app/community_guidelines.py` to include both underscore and slash formats of category keys:

- Added underscore-based category keys (e.g., `harassment_threatening`, `self_harm`) to both `GUIDELINES` and `SHORT_GUIDELINES` dictionaries
- Maintained original slash-based keys (e.g., `harassment/threatening`, `self-harm`) for backward compatibility
- All categories now have proper Chinese translations

### 2. Notification System
The `category_map` in `main.py` was already configured to support both formats:

- Includes underscore format (as returned by the API): 
  - `harassment_threatening` → "🔪 威脅性騷擾"
  - `self_harm` → "💔 自我傷害相關內容"
  - etc.
  
- Maintains slash format (original):
  - `harassment/threatening` → "🔪 威脅性騷擾"
  - `self-harm` → "💔 自我傷害相關內容"
  - etc.

## Technical Details

### API Format
The OpenAI Moderation API returns violation categories with underscores:
- `harassment_threatening`
- `self_harm`
- `self_harm_intent`
- `illicit_violent`
- etc.

### Implementation
Both formats are now supported throughout the system:
1. Direct message notifications will display proper Chinese translations for all violation categories
2. Community guidelines lookup functions will work with either format
3. Emoji indicators are consistently applied across both formats

## Impact
This update ensures:
1. All violation categories returned by the OpenAI API are properly translated to Chinese
2. No missing categories in DM notifications
3. Backward compatibility is maintained
4. Consistent presentation of violation types to users

## No API Changes
This update does not change any API endpoints or parameters. It is purely an internal enhancement to improve the handling of violation categories from the OpenAI Moderation API. 