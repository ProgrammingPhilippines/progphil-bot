package org.progphil.bot.repositories

import org.progphil.bot.commands.PingCommand
import org.progphil.bot.nexus

object CommandRepository {

    fun handshake() {
        nexus.listenMany(
            PingCommand
        )
    }

}