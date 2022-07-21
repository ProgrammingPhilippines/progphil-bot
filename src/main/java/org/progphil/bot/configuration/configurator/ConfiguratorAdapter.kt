package org.progphil.bot.configuration.configurator

interface ConfiguratorAdapter<Type> {

    /**
     * Transforms the provided key-value pair's value into the type that is wanted by the given
     * field in the configuration class. For example, if you want to convert a custom format of string value
     * into a custom class then you can use this to tell the configurator how to convert the value to
     * the class properly.
     *
     * @param key           The key of this pair.
     * @param value         The value of this pair.
     * @param configurator  The [Configurator] instance for when needed to collect another value.
     * @return The intended return value for this pair.
     */
    fun transform(key: String, value: String, configurator: Configurator): Type

}