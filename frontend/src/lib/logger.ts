import { LogLayer, ConsoleTransport } from 'loglayer';

/**
 * Global logger instance for the frontend.
 * Using verified LogLayer v9 initialization pattern with flexible metadata.
 */
function initializeLogger() {
  try {
    const consoleTransport = new ConsoleTransport({
      id: 'console',
      logger: console,
    });

    const baseLogger = new LogLayer({
      transport: [consoleTransport],
      errorFieldName: 'error',
      metadataFieldName: 'metadata',
      enabled: true,
    }).withContext({
      app: 'vellum-frontend',
      env: import.meta.env.MODE,
    });

    // Create a flexible wrapper that accepts any metadata
    return {
      info: (message: string, metadata?: unknown) => {
        if (metadata) {
          baseLogger.withMetadata(metadata as Record<string, unknown>).info(message);
        } else {
          baseLogger.info(message);
        }
      },
      warn: (message: string, metadata?: unknown) => {
        if (metadata) {
          baseLogger.withMetadata(metadata as Record<string, unknown>).warn(message);
        } else {
          baseLogger.warn(message);
        }
      },
      error: (message: string, metadata?: unknown) => {
        if (metadata) {
          baseLogger.withMetadata(metadata as Record<string, unknown>).error(message);
        } else {
          baseLogger.error(message);
        }
      },
      debug: (message: string, metadata?: unknown) => {
        if (metadata) {
          baseLogger.withMetadata(metadata as Record<string, unknown>).debug(message);
        } else {
          baseLogger.debug(message);
        }
      },
      fatal: (message: string, metadata?: unknown) => {
        if (metadata) {
          baseLogger.withMetadata(metadata as Record<string, unknown>).fatal(message);
        } else {
          baseLogger.fatal(message);
        }
      },
    };
  } catch (e) {
    console.warn("LogLayer failed to initialize, falling back to raw console:", e);
    // Basic shim for LogLayer methods to prevent application crashes
    return {
      info: (message: string, metadata?: unknown) => console.log(message, metadata),
      warn: (message: string, metadata?: unknown) => console.warn(message, metadata),
      error: (message: string, metadata?: unknown) => console.error(message, metadata),
      debug: (message: string, metadata?: unknown) => console.debug(message, metadata),
      fatal: (message: string, metadata?: unknown) => console.error(message, metadata),
    };
  }
}

export const logger = initializeLogger();

if (import.meta.env.DEV) {
  logger.info('Logger initialized');
}
