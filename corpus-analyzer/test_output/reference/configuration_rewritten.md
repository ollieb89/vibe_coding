---
title: Configuration Management - UnifiedConfig Pattern
source: skills/backend-dev-guidelines/resources/configuration.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.95)
- Secondary Category: howto (confidence: 0.76)
- Key Features: api_patterns (0.35), code_examples (0.45)

---

```markdown
# Configuration Management - UnifiedConfig Pattern

A comprehensive guide to managing configuration in backend microservices using the UnifiedConfig pattern.

## Table of Contents

- [Overview of UnifiedConfig](#overview-of-unifiedconfig)
  * [Why Use UnifiedConfig?](#why-use-unifiedconfig)
  * [Benefits of Using UnifiedConfig](#benefits-of-using-unifiedconfig)
- [Avoiding Direct Use of process.env](#avoiding-direct-use-of-processenv)
  * [The Rule](#the-rule)
  * [Why This Matters](#why-this-matters)
- [Configuration Structure](#configuration-structure)
  * [UnifiedConfig Interface](#unifiedconfig-interface)
  * [Implementation Pattern](#implementation-pattern)
- [Environment-Specific Configurations](#environment-specific-configurations)
  * [config.ini Structure](#configini-structure)
  * [Environment Overrides](#environment-overrides)
- [Secrets Management](#secrets-management)
  * [DO NOT Commit Secrets](#do-not-commit-secrets)
  * [Use Environment Variables in Production](#use-environment-variables-in-production)
- [Migration Guide](#migration-guide)
  * [Find All process.env Usage](#find-all-processenv-usage)
  * [Migration Example](#migration-example)
- [Related Files](#related-files)

---

## Overview of UnifiedConfig

### Why Use UnifiedConfig?

**Problems with process.env:**
- ❌ No type safety
- ❌ No validation
- ❌ Hard to test
- ❌ Scattered throughout code
- ❌ No default values
- ❌ Runtime errors for typos

**Benefits of using UnifiedConfig:**
- ✅ Type-safe configuration
- ✅ Single source of truth
- ✅ Validated at startup
- ✅ Easy to test with mocks
- ✅ Clear structure
- ✅ Fallback to environment variables

### Benefits of Using UnifiedConfig

UnifiedConfig offers a structured, type-safe approach to managing configuration in backend microservices. It provides a centralized location for all configuration options and ensures that they are validated at startup. This makes it easier to test the application and reduces the likelihood of runtime errors caused by typos or missing values.

---

## Avoiding Direct Use of process.env

### The Rule

```typescript
// ❌ NEVER DO THIS
const timeout = parseInt(process.env.TIMEOUT_MS || '5000');
const dbHost = process.env.DB_HOST || 'localhost';

// ✅ ALWAYS DO THIS
import { config } from './config/unifiedConfig';
const timeout = config.timeouts.default;
const dbHost = config.database.host;
```

### Why This Matters

**Example of problems:**
```typescript
// Typo in environment variable name
const host = process.env.DB_HSOT; // undefined! No error!

// Type safety
const port = process.env.PORT; // string! Need parseInt
const timeout = parseInt(process.env.TIMEOUT); // NaN if not set!
```

**With UnifiedConfig:**
```typescript
const port = config.server.port; // number, guaranteed
const timeout = config.timeouts.default; // number, with fallback
```

---

## Configuration Structure

### UnifiedConfig Interface

```typescript
export interface UnifiedConfig {
    database: {
        host: string;
        port: number;
        username: string;
        password: string;
        database: string;
    };
    server: {
        port: number;
        sessionSecret: string;
    };
    tokens: {
        jwt: string;
        inactivity: string;
        internal: string;
    };
    keycloak: {
        realm: string;
        client: string;
        baseUrl: string;
        secret: string;
    };
    aws: {
        region: string;
        emailQueueUrl: string;
        accessKeyId: string;
        secretAccessKey: string;
    };
    sentry: {
        dsn: string;
        environment: string;
        tracesSampleRate: number;
    };
    // ... more sections
}
```

### Implementation Pattern

**File:** `/blog-api/src/config/unifiedConfig.ts`

```typescript
import * as fs from 'fs';
import * as path from 'path';
import * as ini from 'ini';

const configPath = path.join(__dirname, '../../config.ini');
const iniConfig = ini.parse(fs.readFileSync(configPath, 'utf-8'));

export const config: UnifiedConfig = {
    database: {
        host: iniConfig.database?.host || process.env.DB_HOST || 'localhost',
        port: parseInt(iniConfig.database?.port || process.env.DB_PORT || '3306'),
        username: iniConfig.database?.username || process.env.DB_USER || 'root',
        password: iniConfig.database?.password || process.env.DB_PASSWORD || '',
        database: iniConfig.database?.database || process.env.DB_NAME || 'blog_dev',
    },
    server: {
        port: parseInt(iniConfig.server?.port || process.env.PORT || '3002'),
        sessionSecret: iniConfig.server?.sessionSecret || process.env.SESSION_SECRET || 'dev-secret',
    },
    // ... more configuration
};

// Validate critical config
if (!config.tokens.jwt) {
    throw new Error('JWT secret not configured!');
}
```

**Key Points:**
- Read from `config.ini` first
- Fallback to process.env
- Default values for development
- Validation at startup
- Type-safe access

---

## Environment-Specific Configurations

### config.ini Structure

```ini
[database]
host = localhost
port = 3306
username = root
password = password1
database = blog_dev

[server]
port = 3002
sessionSecret = your-secret-here

[tokens]
jwt = your-jwt-secret
inactivity = 30m
internal = internal-api-token

[keycloak]
realm = myapp
client = myapp-client
baseUrl = https://my-keycloak.com
secret = secret123456

[aws]
region = us-west-2
accessKeyId = ACCESS_KEY_ID
secretAccessKey = SECRET_ACCESS_KEY

[sentry]
dsn = your-sentry-dsn
environment = production
tracesSampleRate = 1.0
```

### Environment Overrides

You can override configuration values specific to your environment by setting environment variables. For example, to override the `database.host` value for a development environment, you would set the following environment variable:

```bash
DB_HOST=my-development-db.com
```

---

## Secrets Management

### DO NOT Commit Secrets

Never commit sensitive information like API keys, database passwords, or other secrets directly to your code repository. Always use environment variables or secure secret management solutions to store and manage these values.

### Use Environment Variables in Production

In production environments, set environment variables for all sensitive configuration options. This ensures that the secrets are not exposed in your code repository and are only accessible by the running application.

---

## Migration Guide

### Find All process.env Usage

To find all instances where `process.env` is being used in your codebase, you can run the following command:

```bash
grep -Rni 'process\.env' .
```

### Migration Example

**Before:**
```typescript
// Scattered throughout code
const timeout = parseInt(process.env.OPENID_HTTP_TIMEOUT_MS || '15000');
const keycloakUrl = process.env.KEYCLOAK_BASE_URL;
const jwtSecret = process.env.JWT_SECRET;
```

**After:**
```typescript
import { config } from './config/unifiedConfig';

const timeout = config.keycloak.timeout;
const keycloakUrl = config.keycloak.baseUrl;
const jwtSecret = config.tokens.jwt;
```

**Benefits:**
- Type-safe
- Centralized
- Easy to test
- Validated at startup

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [testing-guide.md](testing-guide.md)

[source: skills/backend-dev-guidelines/resources/configuration.md]
```