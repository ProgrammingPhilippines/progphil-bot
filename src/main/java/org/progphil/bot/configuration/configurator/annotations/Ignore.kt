package org.progphil.bot.configuration.configurator.annotations

/**
 * An annotation that is used to tell the Configurator to ignore the field that is being annotated here. This
 * will allow the configurator to skip the field entirely.
 */
@Target(AnnotationTarget.FIELD)
@Retention(AnnotationRetention.RUNTIME)
annotation class Ignore()
