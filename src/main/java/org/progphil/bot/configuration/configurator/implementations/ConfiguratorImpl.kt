package org.progphil.bot.configuration.configurator.implementations

import org.progphil.bot.configuration.configurator.Configurator
import org.progphil.bot.configuration.configurator.ConfiguratorAdapters.adapters
import org.progphil.bot.configuration.configurator.annotations.Ignore
import org.progphil.bot.configuration.configurator.annotations.Key
import org.progphil.bot.configuration.configurator.annotations.Required
import org.progphil.bot.logger
import java.io.File
import java.nio.file.Files
import java.util.*
import kotlin.system.exitProcess

class ConfiguratorImpl(file: File) : Configurator {
    private val environments: MutableMap<String, String> = mutableMapOf()

    init {
        if (file.exists()) {
            Files.newBufferedReader(file.toPath()).use { reader ->
                reader.lines()
                    .filter { line: String -> line.contains("=") && !line.startsWith("#") }
                    .map { line: String -> line.split("=", ignoreCase = true, limit = 2) }

                    .forEach { pair ->
                        if (pair.size < 2) {
                            environments[pair[0].lowercase()] = ""
                            return@forEach
                        }

                        environments[pair[0].lowercase()] = pair[1]
                    }
            }
        }
    }

    override fun mirror(toClass: Class<*>) {
        Arrays.stream(toClass.declaredFields).forEachOrdered { field ->
            if (field.isAnnotationPresent(Ignore::class.java)) {
                return@forEachOrdered
            }

            if (field.trySetAccessible()) {
                var name = field.name

                if (field.isAnnotationPresent(Key::class.java)) {
                    name = field.getAnnotation(Key::class.java).value
                }

                val value = get(name)
                if (value == null && field.isAnnotationPresent(Required::class.java)) {
                    logger.error("The configurator cannot find any value for the required field. [field=$name]")
                    exitProcess(1)
                }

                try {
                    val type = field.type
                    if (value != null) {
                        if (isTypeEither(type, Boolean::class.java, Boolean::class.javaPrimitiveType)) {
                            field.setBoolean(field, java.lang.Boolean.parseBoolean(value))
                        } else if (isTypeEither(type, Int::class.java, Int::class.javaPrimitiveType)) {
                            field.setInt(field, value.toInt())
                        } else if (isTypeEither(type, Long::class.java, Long::class.javaPrimitiveType)) {
                            field.setLong(field, value.toLong())
                        } else if (isTypeEither(type, Double::class.java, Double::class.javaPrimitiveType)) {
                            field.setDouble(field, value.toDouble())
                        } else if (type == String::class.java) {
                            field[field] = value
                        } else if (adapters.containsKey(type)) {
                            field[field] = adapters[type]!!.transform(name, value, this)
                        } else {
                            logger.error(
                                "The configurator cannot find a proper adapter for a field. " +
                                        "Please ignore the field using Ignore annotation or add an adapter using the ConfiguratorAdapters. " +
                                        "[field=$name]"
                            )
                            exitProcess(1)
                        }
                    }
                } catch (exception: Exception) {
                    logger.error(
                        "Configurator encountered an throwable while attempting to convert a field. [field=$name]",
                        exception
                    )
                    exitProcess(1)
                }
            } else {
                logger.error("Configurator failed to set a field accessible. [field=${field.name}]")
                exitProcess(1)
            }
        }
    }

    override fun get(key: String): String? = environments[key.lowercase()] ?: System.getenv(key)

    /**
     * A convenient helper method to identify whether the type specified is
     * either of these two. This is used against generic types which always has two
     * types of classes.
     *
     * @param type    The type to compare against either.
     * @param typeOne The first type to compare.
     * @param typeTwo The second type to compare.
     * @return Is the type matches either of them?
     */
    private fun isTypeEither(type: Class<*>, typeOne: Class<*>, typeTwo: Class<*>?): Boolean =
        (type == typeOne || type == typeTwo)
}