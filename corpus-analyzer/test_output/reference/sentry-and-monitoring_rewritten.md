---
type: reference
---

# Sentry Integration and Monitoring

Complete guide to error tracking and performance monitoring with Sentry v8.

## Table of Contents

- [Core Principles](#core-principles)
- [Sentry Initialization](#sentry-initialization)
    - [Instrumentation Pattern](#instrumentation-pattern)
- [Error Capture Patterns](#error-capture-patterns)
    - [BaseController Pattern](#basecontroller-pattern)
    - [Workflow Error Handling](#workflow-error-handling)
    - [Service Layer Error Handling](#service-layer-error-handling)
- [Performance Monitoring](#performance-monitoring)
    - [Database Performance Tracking](#database-performance-tracking)
    - [API Endpoint Spans](#api-endpoint-spans)
- [Cron Job Monitoring](#cron-job-monitoring)
- [Error Context Best Practices](#error-context-best-practices)
    - [Rich Context Example](#rich-context-example)
- [Common Mistakes](#common-mistakes)

---

## Core Principles

**MANDATORY**: All errors MUST be captured to Sentry. No exceptions.

**ALL ERRORS MUST BE CAPTURED** - Use Sentry v8 with comprehensive error tracking across all services.

---

## Sentry Initialization

### Instrumentation Pattern

**Location:** `src/instrument.ts` (MUST be first import in server.ts and all cron jobs)

**Template for Microservices:**

```typescript
import * as Sentry from '@sentry/node';
import * as fs from 'fs';
import * as path from 'path';
import * as ini from 'ini';

const sentryConfigPath = path.join(__dirname, '../sentry.ini');
const sentryConfig = ini.parse(fs.readFileSync(sentryConfigPath, 'utf-8'));

Sentry.init({
    dsn: sentryConfig.sentry?.dsn,
    environment: process.env.NODE_ENV || 'development',
    tracesSampleRate: parseFloat(sentryConfig.sentry?.tracesSampleRate || '0.1'),
    profilesSampleRate: parseFloat(sentryConfig.sentry?.profilesSampleRate || '0.1'),

    integrations: [
        ...Sentry.getDefaultIntegrations({}),
        Sentry.extraErrorDataIntegration({ depth: 5 }),
        Sentry.localVariablesIntegration(),
        Sentry.requestDataIntegration({
            include: {
                cookies: false,
                data: true,
                headers: true,
                ip: true,
                query_string: true,
                url: true,
                user: { id: true, email: true, username: true },
            },
        }),
        Sentry.consoleIntegration(),
        Sentry.contextLinesIntegration(),
        Sentry.prismaIntegration(),
    ],

    beforeSend(event, hint) {
        // Filter health checks
        if (event.request?.url?.includes('/healthcheck')) {
            return null;
        }

        // Scrub sensitive headers
        if (event.request?.headers) {
            delete event.request.headers['authorization'];
            delete event.request.headers['cookie'];
        }

        // Mask emails for PII
        if (event.user?.email) {
            event.user.email = event.user.email.replace(/^(.{2}).*(@.*)$/, '$1***$2');
        }

        return event;
    },

    ignoreErrors: [
        /^Invalid JWT/,
        /^JWT expired/,
        'NetworkError',
    ],
});

// Set service context
Sentry.setTags({
    service: 'form',
    version: '1.0.1',
});

Sentry.setContext('runtime', {
    node_version: process.version,
    platform: process.platform,
});
```

---

## Error Capture Patterns

### BaseController Pattern

```typescript
// Use BaseController.handleError
protected handleError(error: unknown, res: Response, context: string, statusCode = 500): void {
    Sentry.withScope((scope) => {
        scope.setTag('controller', this.constructor.name);
        scope.setTag('operation', context);
        scope.setUser({ id: res.locals?.claims?.userId });
        Sentry.captureException(error);
    });

    res.status(statusCode).json({
        success: false,
        error: { message: error instanceof Error ? error.message : 'An error occurred' }
    });
}
```

---

[source: skills/backend-dev-guidelines/resources/sentry-and-monitoring.md]