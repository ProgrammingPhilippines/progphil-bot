package org.progphil.bot

import ch.qos.logback.classic.Logger
import org.javacord.api.DiscordApi
import org.javacord.api.DiscordApiBuilder
import org.javacord.api.Javacord
import org.javacord.api.util.logging.ExceptionLogger
import org.progphil.bot.configuration.Configuration
import org.progphil.bot.configuration.configurator.Configurator
import org.slf4j.LoggerFactory
import pw.mihou.nexus.Nexus

val logger = LoggerFactory.getLogger("ProgPhil Bot") as Logger
val nexus = Nexus.builder().build()

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
    logger.info("I have logged in on shard ${shard.totalShards}.")
    shard.setAutomaticMessageCacheCleanupEnabled(true)
    shard.setMessageCacheSize(10, 60 * 60)
    shard.setReconnectDelay { it * 2 }
}

// This is where you can store fields that doesn't need to be in the package-level.
// It is currently unused, so this exists but please remove this comment once used.
@Suppress("UNUSED")
object ProgPhilBot {
}