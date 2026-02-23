---
title: Shopify App Development Reference
description: Comprehensive guide for building Shopify apps with OAuth, GraphQL/REST APIs, webhooks, and billing.
tags: app-development, shopify, oauth, graphql, rest-apis, webhooks, billing
---

# App Development Reference

This document provides a comprehensive guide for building Shopify apps with OAuth, GraphQL/REST APIs, webhooks, and billing.

## OAuth Authentication

### OAuth 2.0 Flow

**1. Redirect to Authorization URL:**

```
https://{shop}.myshopify.com/admin/oauth/authorize?client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={REDIRECT_URI}
```

**2. User grants permissions and is redirected to the specified Redirect URI.**

### Token Exchange

**Access Token:**

```
https://{shop}.myshopify.com/admin/oauth/access_token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={CODE}
```

**Refresh Token:**

```
https://{shop}.myshopify.com/admin/oauth/refresh_token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&refresh_token={REFRESH_TOKEN}
```

## GraphQL API

### Query Costs and Rate Limiting

**Check Cost:**

```javascript
const response = await graphqlRequest(shop, token, query);
const cost = response.extensions?.cost;

console.log(`Cost: ${cost.actualQueryCost}/${cost.throttleStatus.maximumAvailable}`);
```

**Handle Throttling:**

```javascript
async function graphqlWithRetry(shop, token, query, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await graphqlRequest(shop, token, query);
    } catch (error) {
      if (error.message.includes("Throttled") && i < retries - 1) {
        await sleep(Math.pow(2, i) * 1000); // Exponential backoff
        continue;
      }
      throw error;
    }
  }
}
```

### App Charges

**One-time Charge:**

```graphql
mutation CreateCharge($input: AppPurchaseOneTimeInput!) {
  appPurchaseOneTimeCreate(input: $input) {
    appPurchaseOneTime {
      id
      name
      price {
        amount
      }
      status
      confirmationUrl
    }
    userErrors {
      field
      message
    }
  }
}
```

Variables:

```json
{
  "input": {
    "name": "Premium Feature",
    "price": { "amount": 49.99, "currencyCode": "USD" },
    "returnUrl": "https://your-app.com/billing/callback"
  }
}
```

**Recurring Charge (Subscription):**

```graphql
mutation CreateSubscription(
  $name: String!
  $returnUrl: URL!
  $lineItems: [AppSubscriptionLineItemInput!]!
  $trialDays: Int
) {
  appSubscriptionCreate(
    name: $name
    returnUrl: $returnUrl
    lineItems: $lineItems
    trialDays: $trialDays
  ) {
    appSubscription {
      id
      name
      status
    }
    confirmationUrl
    userErrors {
      field
      message
    }
  }
}
```

Variables:

```json
{
  "name": "Monthly Subscription",
  "returnUrl": "https://your-app.com/billing/callback",
  "trialDays": 7,
  "lineItems": [
    {
      "plan": {
        "appRecurringPricingDetails": {
          "price": { "amount": 29.99, "currencyCode": "USD" },
          "interval": "EVERY_30_DAYS"
        }
      }
    }
  ]
}
```

**Usage-based Billing:**

```graphql
mutation CreateUsageCharge(
  $subscriptionLineItemId: ID!
  $price: MoneyInput!
  $description: String!
) {
  appUsageRecordCreate(
    subscriptionLineItemId: $subscriptionLineItemId
    price: $price
    description: $description
  ) {
    appUsageRecord {
      id
      price {
        amount
        currencyCode
      }
      description
    }
    userErrors {
      field
      message
    }
  }
}
```

Variables:

```json
{
  "subscriptionLineItemId": "gid://shopify/AppSubscriptionLineItem/123",
  "price": { "amount": "5.00", "currencyCode": "USD" },
  "description": "100 API calls used"
}
```

## Webhooks

### Common Webhook Topics

**Orders:**

- `orders/create`, `orders/updated`, `orders/delete`
- `orders/paid`, `orders/cancelled`, `orders/fulfilled`

**Products:**

- `products/create`, `products/update`, `products/delete`

**Customers:**

- `customers/create`, `customers/update`, `customers/delete`

**Inventory:**

- `inventory_levels/update`

**App:**

- `app/uninstalled` (critical for cleanup)

### Webhook Delivery Failures

Handle delivery failures by:

1. Logging the failure event
2. Retrying the webhook delivery, if necessary
3. Notifying the merchant of the issue

## Best Practices

**Security:**

- Store credentials in environment variables
- Verify webhook HMAC signatures
- Validate OAuth state parameter
- Use HTTPS for all endpoints
- Implement rate limiting on your endpoints

**Performance:**

- Cache access tokens securely
- Use bulk operations for large datasets
- Implement pagination for queries
- Monitor GraphQL query costs

**Reliability:**

- Implement exponential backoff for retries
- Handle webhook delivery failures
- Log errors for debugging
- Monitor app health metrics

**Compliance:**

- Implement GDPR webhooks (mandatory)
- Handle customer data deletion requests
- Provide data export functionality
- Follow data retention policies

[source: skills/shopify-development/references/app-development.md]