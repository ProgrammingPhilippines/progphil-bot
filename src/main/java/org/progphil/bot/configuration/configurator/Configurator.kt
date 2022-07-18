package org.progphil.bot.configuration.configurator

import org.progphil.bot.configuration.configurator.implementations.ConfiguratorImpl
import java.io.File

interface Configurator {

    companion object {

        fun create() = ConfiguratorImpl(File(".env"))

    }

    /**
     * Mirrors the matched configuration fields to the fields that matches on the provided class, this matches it either
     * through the field's name or when annotated then will utilize the
     * [org.progphil.bot.configuration.configurator.annotations.Key] annotation's value.
     *
     * @param toClass The class to mirror the values into.
     */
    fun mirror(toClass: Class<*>)

    /**
     * Gets the value of the environment key provided in the parameters, this performs a look-up in the System Environment
     * Variables if it cannot find any values from the `.env` file provided.
     *
     * @param key The key to look up for the value in the environment variables loaded.
     * @return The value of the key.
     */
    operator fun get(key: String): String?

}