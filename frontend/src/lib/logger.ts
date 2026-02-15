import { LogLayer, ConsoleTransport } from 'loglayer';

/**
 * Global logger instance for the frontend.
 * Using verified LogLayer v9 initialization pattern.
 */
function initializeLogger() {
  try {
    const consoleTransport = new ConsoleTransport({
      id: 'console',
      logger: console,
    });

    return new LogLayer({
      transport: [consoleTransport],
      errorFieldName: 'error',
      metadataFieldName: 'metadata',
      enabled: true,
    }).withContext({
      app: 'vellum-frontend',
      env: import.meta.env.MODE,
    });
  } catch (e) {
    console.warn("LogLayer failed to initialize, falling back to raw console:", e);
    // Basic shim for LogLayer methods to prevent application crashes
    const shim = {
      info: console.log.bind(console),
      warn: console.warn.bind(console),
      warning: console.warn.bind(console),
      error: console.error.bind(console),
      debug: console.debug.bind(console),
      fatal: console.error.bind(console),
      withContext: () => shim,
      withMetadata: () => shim,
      withError: () => shim,
      metadataOnly: () => shim,
      errorOnly: () => shim,
      child: () => shim,
    };
    return shim;
  }
}

export const logger = initializeLogger();

if (import.meta.env.DEV) {
  logger.info('Logger initialized');
}
