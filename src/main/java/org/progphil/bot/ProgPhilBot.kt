package org.progphil.bot

import ch.qos.logback.classic.Logger
import org.javacord.api.DiscordApi
import org.javacord.api.DiscordApiBuilder
import org.javacord.api.Javacord
import org.javacord.api.util.logging.ExceptionLogger
import org.progphil.bot.configuration.Configuration
import org.progphil.bot.configuration.configurator.Configurator
import org.progphil.bot.repositories.CommandRepository
import org.slf4j.LoggerFactory
import pw.mihou.nexus.Nexus
import pw.mihou.nexus.features.command.facade.NexusCommand

val logger = LoggerFactory.getLogger("ProgPhil Bot") as Logger
val nexus: Nexus = Nexus.builder().build()

fun main() {
    Configurator.create().mirror(Configuration::class.java)

    logger.info("""
        
        (っ◔◡◔)っ ProgPhil Bot
        
         ૮˶ᵔᵕᵔ˶ა Environment
         
         Javacord: [
         =  Version         : ${Javacord.VERSION}
         =  Display Version : ${Javacord.DISPLAY_VERSION}
         ]
         
         Discord: [
         =  Gateway         : ${Javacord.DISCORD_GATEWAY_VERSION}
         =  API             : ${Javacord.DISCORD_API_VERSION}
         =  Shards          : ${Configuration.DISCORD_SHARDS}
         ]
         
    """.trimIndent())

    CommandRepository.handshake()

    DiscordApiBuilder()
        .setToken(Configuration.DISCORD_TOKEN)
        .setTotalShards(Configuration.DISCORD_SHARDS)
        .addListener(nexus)
        .loginAllShards()
        .forEach { future -> future.thenAccept { shard ->
            nexus.shardManager.put(shard)
            onShardLogin(shard)
        }.exceptionally(ExceptionLogger.get()) }
}

private fun onShardLogin(shard: DiscordApi) {
    if (shard.currentShard == 0) {
        val commands = nexus.commandManager.commands
            .filter { nexusCommand: NexusCommand ->
                nexusCommand.serverIds.isEmpty()
            }
            .map { obj: NexusCommand -> obj.asSlashCommand() }
            .toList()

        logger.info("I am sending over ${commands.size} commands to Discord to be synchronized!")
        shard.bulkOverwriteGlobalApplicationCommands(
            commands
        ).thenAccept {
            logger.info("I am now synchronized with Discord over ${commands.size} commands wide!")
        }.exceptionally(ExceptionLogger.get())
    }

    logger.info("I have logged in on shard ${shard.totalShards}.")
    shard.setAutomaticMessageCacheCleanupEnabled(true)
    shard.setMessageCacheSize(10, 60 * 60)
    shard.setReconnectDelay { it * 2 }
}

// This is where you can store fields that doesn't need to be in the package-level.
// It is currently unused, so this exists but please remove this comment once used.
@Suppress("UNUSED")
object ProgPhilBot