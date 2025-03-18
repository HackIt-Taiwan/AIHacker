"""
Module for managing user mutes through Discord roles.
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
    Manager for handling user mutes through Discord roles.
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
    
    async def mute_user(self, user: discord.Member, violation_categories: List[str], 
                       content: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Mute a user based on violation.
        
        Args:
            user: Discord user to mute
            violation_categories: List of violation categories
            content: The flagged content (optional)
            details: Additional details about the violation
            
        Returns:
            Tuple containing success status and message
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
            
            # Format a human-readable duration string
            if duration:
                if duration.total_seconds() < 3600:
                    duration_str = f"{int(duration.total_seconds() / 60)} 分鐘"
                elif duration.total_seconds() < 86400:
                    duration_str = f"{int(duration.total_seconds() / 3600)} 小時"
                else:
                    duration_str = f"{int(duration.total_seconds() / 86400)} 天"
            else:
                duration_str = "永久"
            
            # Get or create mute role
            mute_role = await self.get_mute_role(guild)
            if not mute_role:
                return False, "無法創建或獲取禁言角色"
            
            # Add role to user
            await user.add_roles(mute_role, reason=f"內容審核 - 第 {violation_count} 次違規")
            
            # Add mute record to database
            self.db.add_mute(user.id, guild.id, violation_count, duration)
            
            # If temporary mute, schedule unmute task
            if duration:
                # Schedule unmute task
                self.bot.loop.create_task(
                    self._schedule_unmute(user, mute_role, duration)
                )
            
            # Create success message
            from app.community_guidelines import format_mute_reason
            return True, format_mute_reason(violation_count, violation_categories)
        
        except Exception as e:
            logger.error(f"Error muting user {user.name}: {str(e)}")
            return False, f"無法禁言使用者：{str(e)}"
    
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
                        value="請遵守社群規範，避免再次違規。如有任何問題，請聯繫管理員。",
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
                
                # Remove role if user has it
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
                            value="請遵守社群規範，避免再次違規。如有任何問題，請聯繫管理員。",
                            inline=False
                        )
                        
                        await user.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Failed to send unmute DM to {user.name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error checking expired mutes: {str(e)}")
    
    def close(self):
        """Close the database connection."""
        self.db.close()