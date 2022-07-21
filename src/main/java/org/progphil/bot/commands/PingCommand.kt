package org.progphil.bot.commands

import org.javacord.api.util.logging.ExceptionLogger
import pw.mihou.nexus.features.command.facade.NexusCommandEvent
import pw.mihou.nexus.features.command.facade.NexusHandler

@Suppress("UNUSED")
object PingCommand: NexusHandler {

    private const val name: String = "ping"
    private const val description = "Pings the bot to see whether it's still alive or not."

    override fun onEvent(event: NexusCommandEvent) {
        event.respondNowAsEphemeral().setContent("PONG!").respond().exceptionally(ExceptionLogger.get())
    }
}