"""
Module for managing user mutes through Discord roles and timeouts.
"""

import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Tuple
from app.moderation_db import ModerationDB
from app.config import MUTE_ROLE_ID

logger = logging.getLogger(__name__)

class MuteManager:
    """
    Manager for handling user mutes through Discord roles and timeouts.
    """
    
    def __init__(self, bot, mute_role_name: str = "Muted"):
        """
        Initialize the mute manager.
        
        Args:
            bot: Discord bot instance
            mute_role_name: Name of the role to use for muting users
        """
        self.bot = bot
        self.mute_role_name = mute_role_name
        self.mute_role_id = MUTE_ROLE_ID
        self.db = ModerationDB()
        self.guild_mute_roles = {}  # Cache for mute roles by guild
    
    async def get_mute_role(self, guild: discord.Guild) -> discord.Role:
        """
        Get or create the mute role for a guild.
        
        Args:
            guild: Discord guild
            
        Returns:
            The mute role
        """
        # Check cache first
        if guild.id in self.guild_mute_roles:
            return self.guild_mute_roles[guild.id]
        
        # If a specific role ID is configured, use that
        if self.mute_role_id:
            role = guild.get_role(self.mute_role_id)
            if role:
                logger.info(f"Using existing mute role with ID {self.mute_role_id} in guild {guild.name}")
                self.guild_mute_roles[guild.id] = role
                return role
        
        # Otherwise look for a role by name
        role = discord.utils.get(guild.roles, name=self.mute_role_name)
        
        # Create role if it doesn't exist
        if not role:
            try:
                # Create role with permissions that prevent sending messages
                role = await guild.create_role(
                    name=self.mute_role_name,
                    reason="Created for moderation purposes"
                )
                
                # Update permissions for all text channels
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel):
                        try:
                            await channel.set_permissions(
                                role,
                                send_messages=False,
                                add_reactions=False,
                                speak=False
                            )
                        except Exception as e:
                            logger.error(f"Failed to set permissions for channel {channel.name}: {str(e)}")
                
                logger.info(f"Created mute role in guild {guild.name}")
            except Exception as e:
                logger.error(f"Failed to create mute role in guild {guild.name}: {str(e)}")
                return None
        
        # Cache the role
        self.guild_mute_roles[guild.id] = role
        return role
    
    async def timeout_user(self, user: discord.Member, duration: Optional[timedelta] = None, 
                          reason: Optional[str] = None) -> Tuple[bool, str]:
        """
        Apply timeout to a user using Discord's built-in timeout feature.
        
        Args:
            user: Discord user to timeout
            duration: Duration of the timeout
            reason: Reason for the timeout
            
        Returns:
            Tuple containing success status and message
        """
        try:
            # Set the timeout
            timeout_until = discord.utils.utcnow() + duration
            await user.timeout(timeout_until, reason=reason)
            
            # Format a user-friendly message
            if duration.total_seconds() < 3600:
                duration_str = f"{int(duration.total_seconds() / 60)} 分鐘"
            elif duration.total_seconds() < 86400:
                duration_str = f"{int(duration.total_seconds() / 3600)} 小時"
            else:
                duration_str = f"{int(duration.total_seconds() / 86400)} 天"
            return True, f"使用者已被禁言 {duration_str}"
                
        except discord.Forbidden:
            return False, "機器人沒有足夠的權限來設置超時"
        except discord.HTTPException as e:
            return False, f"設置超時時發生錯誤: {str(e)}"
        except Exception as e:
            logger.error(f"Error timing out user {user.name}: {str(e)}")
            return False, f"無法禁言使用者: {str(e)}"
    
    async def mute_user(self, user: discord.Member, violation_categories: List[str], 
                       content: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[bool, str, Optional[discord.Embed]]:
        """
        Mute a user based on violation using Discord's timeout feature.
        
        Args:
            user: Discord user to mute
            violation_categories: List of violation categories
            content: The flagged content (optional)
            details: Additional details about the violation
            
        Returns:
            Tuple containing success status, message, and mute notification embed (if successful)
        """
        try:
            guild = user.guild
            
            # Add violation to database
            self.db.add_violation(
                user_id=user.id,
                guild_id=guild.id,
                content=content,
                violation_categories=violation_categories,
                details=details
            )
            
            # Get violation count for this user
            violation_count = self.db.get_violation_count(user.id, guild.id)
            
            # Calculate mute duration based on violation count
            duration = self.db.calculate_mute_duration(violation_count)
            
            # Format reason
            from app.community_guidelines import format_mute_reason
            reason = format_mute_reason(violation_count, violation_categories)
            
            # Apply timeout using Discord's built-in timeout feature
            success, message = await self.timeout_user(user, duration, reason=f"內容審核 - 第 {violation_count} 次違規")
            
            # Create mute notification embed but don't send it right away
            mute_embed = None
            if success:
                # Add mute record to database
                self.db.add_mute(user.id, guild.id, violation_count, duration)
                
                # Create embed for notification
                mute_embed = discord.Embed(
                    title="禁言通知",
                    description=f"您在 **{guild.name}** 已被暫時禁言。",
                    color=discord.Color.red()
                )
                
                # Add duration if available
                if duration:
                    if duration.total_seconds() < 3600:
                        duration_str = f"{int(duration.total_seconds() / 60)} 分鐘"
                    elif duration.total_seconds() < 86400:
                        duration_str = f"{int(duration.total_seconds() / 3600)} 小時"
                    else:
                        duration_str = f"{int(duration.total_seconds() / 86400)} 天"
                    
                    mute_embed.add_field(
                        name="禁言時間",
                        value=duration_str,
                        inline=True
                    )
                
                mute_embed.add_field(
                    name="原因",
                    value=reason,
                    inline=False
                )
            
            return success, reason, mute_embed
        
        except Exception as e:
            logger.error(f"Error muting user {user.name}: {str(e)}")
            return False, f"無法禁言使用者：{str(e)}", None
    
    async def _schedule_unmute(self, user: discord.Member, mute_role: discord.Role, duration: timedelta):
        """
        Schedule an unmute task after the specified duration.
        
        Args:
            user: Discord user to unmute
            mute_role: The mute role to remove
            duration: Duration before unmuting
        """
        try:
            # Sleep for the duration
            await asyncio.sleep(duration.total_seconds())
            
            # Check if the user still exists and has the mute role
            if user.guild.get_member(user.id) and mute_role in user.roles:
                # Unmute the user
                await user.remove_roles(mute_role, reason="禁言期限已到")
                
                # Send a DM to notify the user
                try:
                    embed = discord.Embed(
                        title="禁言通知",
                        description=f"您在 **{user.guild.name}** 的禁言期限已到，現在已恢復發言權限。",
                        color=discord.Color.green()
                    )
                    
                    embed.add_field(
                        name="請注意",
                        value="請遵守社群規範，避免再次違規。如有任何問題，請聯繫工作人員。",
                        inline=False
                    )
                    
                    await user.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send unmute DM to {user.name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in scheduled unmute for {user.name}: {str(e)}")
    
    async def check_expired_mutes(self):
        """
        Check for expired mutes and unmute users.
        Should be called periodically.
        
        Note: This is not needed for Discord timeouts as they are automatically removed,
        but kept for legacy role-based mutes in the database.
        """
        try:
            # Get expired mutes
            expired_mutes = self.db.check_and_update_expired_mutes()
            
            for mute in expired_mutes:
                user_id = mute['user_id']
                guild_id = mute['guild_id']
                
                # Get guild
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                # Get user
                user = guild.get_member(user_id)
                if not user:
                    continue
                
                # Get mute role
                mute_role = await self.get_mute_role(guild)
                if not mute_role:
                    continue
                
                # Remove the mute role
                if mute_role in user.roles:
                    await user.remove_roles(mute_role, reason="禁言期限已到")
                    
                    # Send a DM to notify the user
                    try:
                        embed = discord.Embed(
                            title="禁言通知",
                            description=f"您在 **{guild.name}** 的禁言期限已到，現在已恢復發言權限。",
                            color=discord.Color.green()
                        )
                        
                        embed.add_field(
                            name="請注意",
                            value="請遵守社群規範，避免再次違規。如有任何問題，請聯繫工作人員。",
                            inline=False
                        )
                        
                        await user.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Failed to send unmute DM to {user.name}: {str(e)}")
            
            # We no longer reapply timeouts after 28 days as per new requirements
            # 28 day timeouts will naturally expire
            # await self.reapply_permanent_timeouts()
                    
        except Exception as e:
            logger.error(f"Error checking expired mutes: {str(e)}")
    
    # This method is no longer used as we don't want to automatically reapply timeouts
    # keeping the code commented for reference
    """
    async def reapply_permanent_timeouts(self):
        # Reapply timeouts for users with permanent bans that are about to expire.
        # Discord only allows timeouts up to 28 days, so we need to reapply them periodically.
        try:
            # Get all active mutes with no end time (permanent bans)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find permanent bans where the last application was more than 20 days ago
            twenty_days_ago = (datetime.utcnow() - timedelta(days=20)).isoformat()
            
            cursor.execute('''
            SELECT user_id, guild_id, id
            FROM mutes 
            WHERE active = TRUE AND end_time IS NULL AND start_time < ?
            ''', (twenty_days_ago,))
            
            permanent_mutes = [dict(row) for row in cursor.fetchall()]
            
            for mute in permanent_mutes:
                user_id = mute['user_id']
                guild_id = mute['guild_id']
                mute_id = mute['id']
                
                # Get guild
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                # Get user
                user = guild.get_member(user_id)
                if not user:
                    continue
                
                # Check if the user is currently timed out
                if user.timed_out:
                    # Calculate remaining timeout time
                    if user.timeout and user.timeout > discord.utils.utcnow():
                        remaining_seconds = (user.timeout - discord.utils.utcnow()).total_seconds()
                        
                        # If more than 7 days remaining, skip reapplication
                        if remaining_seconds > 7 * 24 * 3600:
                            continue
                
                # Reapply the permanent timeout
                logger.info(f"Reapplying permanent timeout for user {user.name} in guild {guild.name}")
                
                # Get violation count and categories for the reason
                violation_count = self.db.get_violation_count(user_id, guild_id)
                
                # Set a new 28-day timeout
                timeout_until = discord.utils.utcnow() + timedelta(days=28)
                try:
                    await user.timeout(timeout_until, reason=f"重新應用永久禁言 - 第 {violation_count} 次違規")
                    
                    # Update the mute record's start time
                    cursor.execute('''
                    UPDATE mutes
                    SET start_time = ?
                    WHERE id = ?
                    ''', (datetime.utcnow().isoformat(), mute_id))
                    
                    conn.commit()
                    
                    logger.info(f"Successfully reapplied permanent timeout for user {user.name}")
                except Exception as e:
                    logger.error(f"Failed to reapply timeout for {user.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error reapplying permanent timeouts: {str(e)}")
    """
    
    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()