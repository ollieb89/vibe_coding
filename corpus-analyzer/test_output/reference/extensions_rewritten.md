---
type: reference
---

# Extensions Reference

Guide for building UI extensions and Shopify Functions.

## Checkout UI Extensions

Customize checkout and thank-you pages with native-rendered components.

### Extension Points

**Block Targets (Merchant-Configurable):**

- `purchase.checkout.block.render` - Main checkout
- `purchase.thank-you.block.render` - Thank you page

**Static Targets (Fixed Position):**

- `purchase.checkout.block.static.header`
- `purchase.checkout.block.static.footer`
- `purchase.checkout.block.static.sidebar`

### Best Practices

- Lazy load data
- Memoize expensive computations
- Use loading states
- Minimize re-renders
- Provide clear error messages
- Show loading indicators
- Validate inputs
- Support keyboard navigation
- Verify session tokens on backend
- Sanitize user input
- Use HTTPS for all requests
- Don't expose sensitive data
- Test on development stores
- Verify mobile/desktop
- Check accessibility
- Test edge cases

## Admin Extensions

Customize the admin interface of your Shopify store.

### Order Status Extension

```javascript
import { useApi } from "@shopify/ui-extensions-react";

function Extension() {
  const { order } = useApi();

  function handleReturn() {
    // Initiate return
  }

  return (
    <BlockStack>
      <Text variant="headingMd">Need to return?</Text>
      <Text>Start return for order {order.name}</Text>
      <Button onPress={handleReturn}>Start Return</Button>
    </BlockStack>
  );
}
```

**Targets:**

- `admin_orders.list.block.render`
- `admin_orders.view.block.render`

## Shopify Functions

Serverless backend customization.

### Function Types

**Discounts:**

- `order_discount` - Order-level discounts
- `product_discount` - Product-specific discounts
- `shipping_discount` - Shipping discounts

**Payment Customization:**

- Hide/rename/reorder payment methods

**Delivery Customization:**

- Custom shipping options
- Delivery rules

**Validation:**

- Cart validation rules
- Checkout validation

### Create Function

```bash
shopify app generate extension --type function
```

### Order Discount Function

```javascript
// input.graphql
query Input {
  cart {
    lines {
      quantity
      merchandise {
        ... on ProductVariant {
          product {
            hasTag(tag: "bulk-discount")
          }
        }
      }
    }
  }
}

// function.js
export default function orderDiscount(input) {
  const targets = input.cart.lines
    .filter(line => line.merchandise.product.hasTag)
    .map(line => ({
      productVariant: { id: line.merchandise.id }
    }));

  if (targets.length === 0) {
    return { discounts: [] };
  }

  return {
    discounts: [{
      targets,
      value: {
        percentage: {
          value: 10  // 10% discount
        }
      }
    }]
  };
}
```

### Payment Customization Function

```javascript
export default function paymentCustomization(input) {
  const hidePaymentMethods = input.cart.lines.some(
    (line) => line.merchandise.product.hasTag,
  );

  if (!hidePaymentMethods) {
    return { operations: [] };
  }

  return {
    operations: [
      {
        hide: {
          paymentMethodId: "gid://shopify/PaymentMethod/123",
        },
      },
    ],
  };
}
```

### Validation Function

```javascript
export default function cartValidation(input) {
  const errors = [];

  // Max 5 items per cart
  if (input.cart.lines.length > 5) {
    errors.push({
      localizedMessage: "Maximum 5 items allowed per order",
      target: "cart",
    });
  }

  // Min $50 for wholesale
  const isWholesale = input.cart.lines.some(
    (line) => line.merchandise.product.hasTag,
  );

  if (isWholesale && input.cart.cost.totalAmount.amount < 50) {
    errors.push({
      localizedMessage: "Wholesale orders require $50 minimum",
      target: "cart",
    });
  }

  return { errors };
}
```

## Network Requests

Extensions can call external APIs.

```javascript
import { useApi } from "@shopify/ui-extensions-react/checkout";

function Extension() {
  const { sessionToken } = useApi();

  async function fetchData() {
    const token = await sessionToken.get();

    const response = await fetch("https://your-app.com/api/data", {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return await response.json();
  }
}
```

## Resources

- Checkout Extensions: https://shopify.dev/docs/api/checkout-extensions
- Admin Extensions: https://shopify.dev/docs/apps/admin/extensions
- Functions: https://shopify.dev/docs/apps/functions
- Components: https://shopify.dev/docs/api/checkout-ui-extensions/components

[source: skills/shopify-development/references/extensions.md]