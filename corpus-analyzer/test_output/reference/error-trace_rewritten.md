---
title: Error Tracking and Monitoring
description: Implement comprehensive error monitoring solutions, including real-time error detection, meaningful alerts, error grouping, performance monitoring, and integration with popular error tracking services.
tags: api_patterns, code_examples
---

# Error Tracking and Monitoring

You are an error tracking and observability expert specializing in implementing comprehensive error monitoring solutions. Set up error tracking systems, configure alerts, implement structured logging, and ensure teams can quickly identify and resolve production issues.

## Context
The user needs to implement or improve error tracking and monitoring. Focus on real-time error detection, meaningful alerts, error grouping, performance monitoring, and integration with popular error tracking services.

## Requirements
[user-defined]

## Instructions

### 1. Error Tracking Analysis

Analyze current error handling and tracking:

**Error Analysis Script**
```python
import os
import re
import ast
from pathlib import Path
from collections import defaultdict

class ErrorTrackingAnalyzer:
    def analyze_codebase(self, project_path):
        """
        Analyze error handling patterns in codebase
        """
        analysis = {
            'error_handling': self._analyze_error_handling(project_path),
            'logging_usage': self._analyze_logging(project_path),
            'monitoring_setup': self._check_monitoring_setup(project_path),
            'error_patterns': self._identify_error_patterns(project_path),
            'recommendations': []
        }
        
        self._generate_recommendations(analysis)
        return analysis
    
    def _analyze_error_handling(self, project_path):
        """Analyze error handling patterns"""
        patterns = {
            'try_catch_blocks': 0,
            'unhandled_promises': 0,
            'unhandled_exceptions': 0,
            'error_types': defaultdict(int)
        }
        ....
```
[source: error-debugging/commands/error-trace.md]

### 2. Error Tracking Setup

Set up an error tracking system using a popular service like Sentry or Rollbar:

**Sentry Middleware (Express.js)**
```javascript
const Sentry = require('@sentry/node');
const { Handlers } = require('@sentry/tracing');

// Initialize Sentry with your DSN
Sentry.init({ dsn: 'YOUR_DSN' });

// Express middleware for capturing requests and errors
app.use(Handlers.requestHandler());
app.use(Handlers.errorHandler({ shouldHandleError: (err) => err.status >= 400 }));
```
[source: error-debugging/commands/error-trace.md]

### 3. Custom Error Tracking Service (Node.js)

Create a custom error tracking service for more granular control over error handling and reporting:

**Custom Error Tracker (TypeScript)**
```typescript
import { captureException, captureMessage } from '@sentry/node';

class CustomErrorTracker {
    constructor(private config: CustomErrorTrackerConfig) {}

    trackException(error: Error) {
        captureException(error);
        this._logEvent({ level: 'error', message: error.message });
    }

    trackMessage(message: string, level: 'info' | 'warning' | 'error') {
        captureMessage(message, level);
        this._logEvent({ level, message });
    }

    private _logEvent(event: Omit<ErrorEvent, 'timestamp'>) {
        // Add current timestamp and other context data to event
        const timestamp = new Date();
        const fullEvent = { ...event, timestamp };
        this._sendEvent(fullEvent);
    }

    private _sendEvent(event: ErrorEvent) {
        if (Math.random() > this.config.sampleRate) return;

        // Filter sensitive data and send event to your error tracking service
        const sanitizedEvent = this._sanitizeEvent(event);
        this._sendToErrorTrackerService(sanitizedEvent);
    }

    private _sanitizeEvent(event: ErrorEvent) {
        // Remove sensitive data from event before sending it to the error tracking service
        ....
    }

    private _sendToErrorTrackerService(event: ErrorEvent) {
        // Send event to your error tracking service (e.g., Sentry, Rollbar, etc.)
        ....
    }
}
```
[source: error-debugging/commands/error-trace.md]