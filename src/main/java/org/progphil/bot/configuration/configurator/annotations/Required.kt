package org.progphil.bot.configuration.configurator.annotations

/**
 * An annotation that is used to tell the Configurator that this field should have a value otherwise
 * throw an error during runtime that the key doesn't have a matching value.
 */
@Retention(AnnotationRetention.RUNTIME)
@Target(AnnotationTarget.FIELD)
annotation class Required()
