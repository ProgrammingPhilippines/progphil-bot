package org.progphil.bot.configuration.configurator.annotations

/**
 * An annotation that is used to indicate that this field's name is not the key
 * that matches in the environment variables but instead is the value indicated or
 * provided in this annotation's value.
 */
@Target(AnnotationTarget.FIELD)
@Retention(AnnotationRetention.RUNTIME)
annotation class Key(val value: String)
