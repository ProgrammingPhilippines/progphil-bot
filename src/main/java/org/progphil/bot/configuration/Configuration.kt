package org.progphil.bot.configuration

import org.progphil.bot.configuration.configurator.annotations.Required

object Configuration {

    @Required
    lateinit var DISCORD_TOKEN: String
    var DISCORD_SHARDS: Int = 1

}