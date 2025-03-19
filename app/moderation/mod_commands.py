"""
Discord moderation commands for administrators and moderators.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class ModerationCommands(commands.Cog):
    """Commands for server moderation."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="timeout", description="超時使用者一段時間，防止他們發送訊息或互動")
    @app_commands.describe(
        user="要超時的使用者",
        minutes="超時時間（分鐘）",
        hours="超時時間（小時）",
        days="超時時間（天）",
        reason="超時的原因"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        minutes: Optional[int] = 0,
        hours: Optional[int] = 0,
        days: Optional[int] = 0,
        reason: Optional[str] = None
    ):
        """
        Timeout a user for a specified duration using Discord's built-in timeout feature.
        
        Args:
            interaction: The Discord interaction
            user: The user to timeout
            minutes: Minutes to timeout (default 0)
            hours: Hours to timeout (default 0)
            days: Days to timeout (default 0)
            reason: Reason for the timeout (optional)
        """
        try:
            # Check permissions
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "你沒有足夠的權限來執行此操作。需要 `moderate_members` 權限。",
                    ephemeral=True
                )
                return
            
            # Calculate total duration
            total_minutes = minutes + (hours * 60) + (days * 24 * 60)
            
            # Check if duration is valid
            if total_minutes <= 0:
                await interaction.response.send_message(
                    "請指定有效的超時時間。至少需要 1 分鐘。",
                    ephemeral=True
                )
                return
            
            # Discord limit is 28 days
            if total_minutes > 28 * 24 * 60:
                await interaction.response.send_message(
                    "超時時間不能超過 28 天。請減少超時時間。",
                    ephemeral=True
                )
                return
            
            # Check if user is the interaction user
            if user.id == interaction.user.id:
                await interaction.response.send_message(
                    "你不能對自己使用超時命令。",
                    ephemeral=True
                )
                return
            
            # Check if user is the bot itself
            if user.id == self.bot.user.id:
                await interaction.response.send_message(
                    "我不能對自己使用超時命令。",
                    ephemeral=True
                )
                return
            
            # Check if user can be timed out (role hierarchy)
            if interaction.guild.me.top_role <= user.top_role:
                await interaction.response.send_message(
                    "我無法超時此使用者，因為他們的最高角色比我的最高角色更高或相同。",
                    ephemeral=True
                )
                return
            
            if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message(
                    "你無法超時此使用者，因為他們的最高角色比你的最高角色更高或相同。",
                    ephemeral=True
                )
                return
            
            # Set timeout
            duration = timedelta(minutes=total_minutes)
            await user.timeout(discord.utils.utcnow() + duration, reason=reason)
            
            # Create success message with duration
            if total_minutes < 60:
                duration_str = f"{total_minutes} 分鐘"
            elif total_minutes < 24 * 60:
                duration_str = f"{total_minutes // 60} 小時 {total_minutes % 60} 分鐘"
            else:
                days = total_minutes // (24 * 60)
                remaining_minutes = total_minutes % (24 * 60)
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                duration_str = f"{days} 天 {hours} 小時 {minutes} 分鐘"
            
            # Create embed
            embed = discord.Embed(
                title="使用者已超時",
                description=f"{user.mention} 已被超時 {duration_str}",
                color=discord.Color.orange()
            )
            
            if reason:
                embed.add_field(name="原因", value=reason, inline=False)
            
            embed.set_footer(text=f"管理員: {interaction.user.name}")
            
            # Respond to the interaction
            await interaction.response.send_message(embed=embed)
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title="你已被超時",
                    description=f"你在 **{interaction.guild.name}** 已被超時 {duration_str}",
                    color=discord.Color.red()
                )
                
                if reason:
                    user_embed.add_field(name="原因", value=reason, inline=False)
                
                user_embed.set_footer(text=f"管理員: {interaction.user.name}")
                
                await user.send(embed=user_embed)
            except discord.Forbidden:
                logger.info(f"Could not DM user {user.name} about timeout")
            except Exception as e:
                logger.error(f"Error sending timeout DM to {user.name}: {str(e)}")
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "我沒有足夠的權限來超時此使用者。請確保我有 `moderate_members` 權限。",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in timeout command: {str(e)}")
            await interaction.response.send_message(
                f"超時使用者時發生錯誤: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="remove_timeout", description="移除使用者的超時")
    @app_commands.describe(
        user="要移除超時的使用者",
        reason="移除超時的原因"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def remove_timeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: Optional[str] = None
    ):
        """
        Remove a timeout from a user.
        
        Args:
            interaction: The Discord interaction
            user: The user to remove timeout from
            reason: Reason for removing the timeout (optional)
        """
        try:
            # Check permissions
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "你沒有足夠的權限來執行此操作。需要 `moderate_members` 權限。",
                    ephemeral=True
                )
                return
            
            # Check if user is timed out
            if not user.is_timed_out():
                await interaction.response.send_message(
                    f"{user.mention} 目前沒有被超時。",
                    ephemeral=True
                )
                return
            
            # Remove timeout
            await user.timeout(None, reason=reason)
            
            # Create embed
            embed = discord.Embed(
                title="超時已移除",
                description=f"{user.mention} 的超時已被移除",
                color=discord.Color.green()
            )
            
            if reason:
                embed.add_field(name="原因", value=reason, inline=False)
            
            embed.set_footer(text=f"管理員: {interaction.user.name}")
            
            # Respond to the interaction
            await interaction.response.send_message(embed=embed)
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title="你的超時已移除",
                    description=f"你在 **{interaction.guild.name}** 的超時已被移除",
                    color=discord.Color.green()
                )
                
                if reason:
                    user_embed.add_field(name="原因", value=reason, inline=False)
                
                user_embed.set_footer(text=f"管理員: {interaction.user.name}")
                
                await user.send(embed=user_embed)
            except discord.Forbidden:
                logger.info(f"Could not DM user {user.name} about timeout removal")
            except Exception as e:
                logger.error(f"Error sending timeout removal DM to {user.name}: {str(e)}")
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "我沒有足夠的權限來移除此使用者的超時。請確保我有 `moderate_members` 權限。",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in remove_timeout command: {str(e)}")
            await interaction.response.send_message(
                f"移除使用者超時時發生錯誤: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Add the moderation commands cog to the bot."""
    await bot.add_cog(ModerationCommands(bot)) 