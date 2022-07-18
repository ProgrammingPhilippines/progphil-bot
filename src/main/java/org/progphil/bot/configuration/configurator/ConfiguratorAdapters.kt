package org.progphil.bot.configuration.configurator

object ConfiguratorAdapters {

    val adapters: MutableMap<Class<*>, ConfiguratorAdapter<*>> = mutableMapOf()

    operator fun get(key: Class<*>) = adapters[key]
    operator fun set(key: Class<*>, value: ConfiguratorAdapter<*>) {
        adapters[key] = value
    }

}